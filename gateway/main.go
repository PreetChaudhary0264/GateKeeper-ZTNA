package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"  //server crash hone prr error print krna, log.fatal()
	"net/http"
	"time"
)

func sendAuditLog(
	email string,
	role string,
	path string,
	deviceID string,
	allowed bool,
	blockedAt string,
	reason string,
) {
	cfg := LoadConfig()                       //config.go file me function ko call kra hai
	auditURL := cfg.AuditServiceURL + "/log"     // = "http://ztna-audit:9999/log"

	payload := map[string]interface{}{
		"email":      email,
		"role":       role,
		"path":       path,
		"device_id":  deviceID,
		"allowed":    allowed,
		"blocked_at": blockedAt,
		"reason":     reason,
	}

	body, _ := json.Marshal(payload) //simple marshal hai fail nhi hoga but production me error check krna shi rhega
	//go object ko json me convert krne ka liye marshal use kiya hai, kyuki payload ek Map hai

	go func() {
		resp, err := http.Post(
			auditURL,
			"application/json",
			bytes.NewBuffer(body),  //http.post ko byte array nhi chaiye kyuki HTTP package stream read karta hai. isko chaiye io.Reader
		)
		if err != nil {
			fmt.Println("Audit log nahi gaya:", err)
			return
		}
		defer resp.Body.Close()  //http response ke ander connection attached hota hai isliye close krna pdega wrna connection leak, memory leak ho skta hai
	}()
}

func main() {
	cfg := LoadConfig()
	
	initRedis(cfg.RedisAddr)  //redis connect kro 
	
	initMTLS()  //gateway certificates load kro, kyuki hr request pe certificate file nhi padhni expensive ho jayga

	fmt.Println("ZTNA Gateway Starting")
	fmt.Printf("Port     : %s\n", cfg.GatewayPort)
	fmt.Printf("Auth     : %s\n", cfg.AuthServiceURL)
	fmt.Printf("Audit    : %s\n", cfg.AuditServiceURL)
	fmt.Printf("Redis    : %s\n", cfg.RedisAddr)
	fmt.Printf("mTLS     : enabled\n")
	fmt.Println("-----------------------------")
    
	//route registration
	http.HandleFunc("/health", healthHandler)  //pehle health check krlo
	http.HandleFunc("/", gatewayHandler)  //then baaki requests yha bhejdo, jaise /admin, /hr, /finance


    log.Fatal(http.ListenAndServe(      // TODO — Gateway should also use HTTPS
        cfg.GatewayPort,                //Step1 port open hoga => 8000
	                                    //step2 TCP socket create
	                                    //step3 Infinite loop => Request wairt
	                                    //step4 request aayi, Matching route find, handler call
        // "/certs/gateway.crt",
        // "/certs/gateway.key",
        nil,
    ))
    }
                   //response bhejne ke liye, incoming request  (same as req,res in express.js)
func gatewayHandler(w http.ResponseWriter, r *http.Request) {
    enableCORS(w) 

	if r.Method == http.MethodOptions {  //browser pehle puchega ki can i send request?,  server => yes
        w.WriteHeader(http.StatusOK)
        return
    }  //hta skte ho bs lga diya aise hi

	cfg := LoadConfig()
	start    := time.Now()
	deviceID := r.Header.Get("X-Device-ID")
	basePath := getBasePath(r.URL.Path)  //request ka path ex=>     /finance/payroll

	fmt.Printf("\n [%s] %s %s\n",
		time.Now().Format("15:04:05"),
		r.Method,
		r.URL.Path,
	)

	// ------------- CHECK 1: AUTH ---------------------
	claims, err := checkAuth(r, cfg.AuthServiceURL)
	if err != nil {
		fmt.Printf("Auth FAILED   : %s\n", err.Error())
		sendAuditLog(
			"anonymous", "unknown", basePath,
			deviceID, false, "auth", err.Error(),
		)
		sendError(w, http.StatusUnauthorized, err.Error(), "auth")
		return
	}
	fmt.Printf("Auth PASSED   : %s (%s)\n", claims.Email, claims.Role)


	// -------------- CHECK 2: DEVICE ------------------
	deviceOk, deviceMsg := checkDevice(r)
	if !deviceOk {
		fmt.Printf("Device FAILED : %s\n", deviceMsg)
		sendAuditLog(
			claims.Email, claims.Role, basePath,
			deviceID, false, "device_check", deviceMsg,
		)
		sendError(w, http.StatusForbidden, deviceMsg, "device_check")
		return
	}
	fmt.Printf("Device PASSED : %s\n", deviceMsg)


	// -------------- CHECK 3: POLICY -----------------
	allowed, policyMsg := checkPolicy(claims.Role, basePath)
	if !allowed {
		fmt.Printf("Policy FAILED : %s\n", policyMsg)
		sendAuditLog(
			claims.Email, claims.Role, basePath,
			deviceID, false, "policy", policyMsg,
		)
		sendError(w, http.StatusForbidden, policyMsg, "policy")
		return
	}
	fmt.Printf("Policy PASSED : %s\n", policyMsg)

	// -------- TEENO CHECK PASS — LOG + FORWARD -----------
	sendAuditLog(
		claims.Email, claims.Role, basePath,
		deviceID, true, "", "Access granted",
	)
	fmt.Printf("FORWARDING   : %s → %s\n", r.URL.Path, claims.Email)
	forwardRequest(w, r, claims)
	fmt.Printf("Time         : %v\n", time.Since(start))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w) 
	cfg := LoadConfig()
	sendJSON(w, map[string]interface{}{
		"status":   "Gateway chal raha hai!",
		"port":     ":8080",
		"auth":     cfg.AuthServiceURL,
		"audit":    cfg.AuditServiceURL,
		"services": Services,
		"time":     time.Now().Format(time.RFC3339),
	})
}