package main

import (
	"bytes"     //http req body bnana
	"context"  //Redis operations ke liye context, timeout aur cancellation handle krta hai
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/go-redis/redis/v8"   //redis client library, token blacklist check krna
)

var ctx = context.Background()   //redis ka her operation context mangta hai

// Redis se baat krne wala global client jab user logout kre to uska token redis me daal do agar dobara login kre to blocked, normally user logout krne ke baad token 15mins tak valid rhega isliye for security
var redisClient *redis.Client

func initRedis(addr string) {
	if addr == "" {
		fmt.Println("❌ CRITICAL: Redis address not configured")
		fmt.Println("Redis is mandatory for ZTNA security (token blacklisting)")
		os.Exit(1)
	}
	
	redisClient = redis.NewClient(&redis.Options{
		Addr: addr,
	})

	_, err := redisClient.Ping(ctx).Result()
	if err != nil {
		fmt.Printf("❌ CRITICAL: Redis connection failed - %v\n", err)
		fmt.Println("Redis is mandatory for ZTNA security (token blacklisting)")
		os.Exit(1)
	}
	
	fmt.Println("✓ Redis connected successfully!")
}

// Auth Service se jo response aayega
//json me fields hongi valid:true, email:xyz@mai.com to mapping kri hai
type AuthResponse struct {
	Valid  bool   `json:"valid"`
	Email  string `json:"email"`
	Role   string `json:"role"`
	Name   string `json:"name"`
}

// Gateway ke andar user ki info carry karne ke liye
//auth service ka response use nhi kr rhe because usme valid fileds bhi hai and aage chlke kya pta orr fields aaye isliye sirf requierd info do jo gateway use krega
type Claims struct {
	Email string
	Role  string
	Name  string
}

// ─── AUTH CHECK ──────────────────────────────
// Gateway khud verify nahi karta
// Auth Service ko call karta hai
func checkAuth(r *http.Request, authServiceURL string) (*Claims, error) {

	// Header se token nikalo
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return nil, fmt.Errorf("Authorization header nahi hai")
	}

	parts := strings.Split(authHeader, " ")
	if len(parts) != 2 || parts[0] != "Bearer" {
		return nil, fmt.Errorf("Format galat hai — 'Bearer TOKEN' chahiye")
	}

	tokenStr := parts[1]

	// Redis blacklist check
	// Token blacklisted hai to block karo
	blocked, err := redisClient.Get(ctx, "blacklist:"+tokenStr).Result()
	if err == nil && blocked != "" {
		return nil, fmt.Errorf("Token blacklisted - user logged out")
	}

	//auth service ko json me bhejenge
	requestBody, _ := json.Marshal(map[string]string{
		"token": tokenStr,
	})
    
	// Auth Service ko call karo verify ke liye
	resp, err := http.Post(
		authServiceURL+"/verify",   // "http://ztna-auth:8001/verify"
		"application/json",         // Content-Type header
		bytes.NewBuffer(requestBody),// Request body
	)

	if err != nil {
		return nil, fmt.Errorf("Auth service se connect nahi ho paya")
	}

// 	HTTP response body ek stream hai
//  Use karne ke baad close karna zaroori hai, wrna memory leak ho skti hai
	defer resp.Body.Close()
    

	// agar status code 200 nhi aaya to ,Auth Service ne reject kiya
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Token invalid ya expire ho gaya")
	}

	// Auth Service ka response parse karo
	var authResp AuthResponse
	if err := json.NewDecoder(resp.Body).Decode(&authResp); err != nil {
		return nil, fmt.Errorf("Auth service ka response samajh nahi aaya")
	}

	return &Claims{
		Email: authResp.Email,
		Role:  authResp.Role,
		Name:  authResp.Name,
	}, nil
}


// ─── DEVICE CHECK ────────────────────────────
func checkDevice(r *http.Request) (bool, string) {

	deviceID := r.Header.Get("X-Device-ID")
	if deviceID == "" {
		return false, "Device ID nahi hai (X-Device-ID header chahiye)"
	}

	deviceOS := r.Header.Get("X-Device-OS")
	if deviceOS == "" {
		return false, "Device OS nahi hai (X-Device-OS header chahiye)"
	}

	// Blacklisted devices, dummy le liye for checking production me database se fetch honge
	blacklisted := []string{"HACKED-001", "UNKNOWN-999"}
	for _, blocked := range blacklisted {
		if deviceID == blocked {
			return false, fmt.Sprintf("Device '%s' blacklisted hai!", deviceID)
		}
	}

	return true, fmt.Sprintf("Device %s (%s) verified", deviceID, deviceOS)
}


// ─── POLICY CHECK ────────────────────────────
func checkPolicy(role string, path string) (bool, string) {

	policies := map[string]map[string]bool{
		"hr": {
			"/hr-portal": true,
			"/finance":   false,
			"/admin":     false,
		},
		"finance": {
			"/hr-portal": false,
			"/finance":   true,
			"/admin":     false,
		},
		"admin": {
			"/hr-portal": true,
			"/finance":   true,
			"/admin":     true,
		},
	}

	rolePolicies, exists := policies[role]
	if !exists {
		return false, fmt.Sprintf("Role '%s' exist nahi karta", role)
	}

	allowed, pathExists := rolePolicies[path]
	if !pathExists {
		return false, fmt.Sprintf("Path '%s' defined nahi hai", path)
	}

	if !allowed {
		return false, fmt.Sprintf("Role '%s' ko '%s' ka access nahi", role, path)
	}

	return true, "Access allowed"
}

// ─── HELPERS ─────────────────────────────────
func sendError(w http.ResponseWriter, statusCode int, message string, step string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(map[string]string{
		"error":      message,
		"blocked_at": step,
		"timestamp":  time.Now().Format(time.RFC3339),
	})
}
//agar koi check fail hua to user ko json error bhejdo

func sendJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
// 	Success response bhejne ke liye
//  used in health check
}

func enableCORS(w http.ResponseWriter) {
    w.Header().Set("Access-Control-Allow-Origin", "*")
    w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Device-ID, X-Device-OS")
}