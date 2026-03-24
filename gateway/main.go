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
	cfg := LoadConfig()
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

	go func() {
		resp, err := http.Post(
			auditURL,
			"application/json",
			bytes.NewBuffer(body),
		)
		if err != nil {
			fmt.Println("Audit log nahi gaya:", err)
			return
		}
		defer resp.Body.Close()  //stream hai to close bhi krna pdega
	}()
}

func main() {
	cfg := LoadConfig()
	
	// Initialize Redis - MANDATORY
	initRedis(cfg.RedisAddr)
	
	initMTLS()  //gateway certificates load kro

	fmt.Println("ZTNA Gateway Starting")
	fmt.Printf("Port     : %s\n", cfg.GatewayPort)
	fmt.Printf("Auth     : %s\n", cfg.AuthServiceURL)
	fmt.Printf("Audit    : %s\n", cfg.AuditServiceURL)
	fmt.Printf("Redis    : %s\n", cfg.RedisAddr)
	fmt.Printf("mTLS     : enabled\n")
	fmt.Println("──────────────────────────────────")
    
	//route registration
	http.HandleFunc("/health", healthHandler)  //pehle health check krlo
	http.HandleFunc("/", gatewayHandler)  //then baaki requests yha bhejdo

	// FIX — Gateway should also use HTTPS
    log.Fatal(http.ListenAndServe(
        cfg.GatewayPort,
        // "/certs/gateway.crt",
        // "/certs/gateway.key",
        nil,
    ))
    }

func gatewayHandler(w http.ResponseWriter, r *http.Request) {
    enableCORS(w) 
	if r.Method == http.MethodOptions {
        w.WriteHeader(http.StatusOK)
        return
    }

	cfg := LoadConfig()
	start    := time.Now()
	deviceID := r.Header.Get("X-Device-ID")
	basePath := getBasePath(r.URL.Path)

	fmt.Printf("\n📥 [%s] %s %s\n",
		time.Now().Format("15:04:05"),
		r.Method,
		r.URL.Path,
	)

	// ─── CHECK 1: AUTH ────────────────────────
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

	// ─── CHECK 2: DEVICE ──────────────────────
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

	// ─── CHECK 3: POLICY ──────────────────────
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

	// ─── TEENO PASS — LOG + FORWARD ───────────
	sendAuditLog(
		claims.Email, claims.Role, basePath,
		deviceID, true, "", "Access granted",
	)
	fmt.Printf("FORWARDING   : %s → %s\n", r.URL.Path, claims.Email)
	forwardRequest(w, r, claims)
	fmt.Printf("⏱Time         : %v\n", time.Since(start))
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