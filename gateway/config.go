package main


import "os"
type Config struct {
	GatewayPort    string
	AuthServiceURL string
	RedisAddr      string
	AuditServiceURL string
}

func LoadConfig() Config {
    redisAddr := getEnv("REDIS_ADDR", "")
    if redisAddr == "" {
        panic("REDIS_ADDR environment variable is required")
    }
    
    return Config{
        GatewayPort:     ":8080",
        AuthServiceURL:  getEnv("AUTH_SERVICE_URL", "http://localhost:8001"),
        RedisAddr:       redisAddr,
        AuditServiceURL: getEnv("AUDIT_SERVICE_URL", "http://localhost:9999"),
    }
}

// Environment variable lo — nahi mila toh default use karo
func getEnv(key, defaultVal string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultVal
}

var Services = map[string]string{
	"/hr-portal": getServiceURL("HR_SERVICE_URL",      "https://localhost:9001"),
	"/finance":   getServiceURL("FINANCE_SERVICE_URL", "https://localhost:9002"),
	"/admin":     getServiceURL("ADMIN_SERVICE_URL",   "https://localhost:9003"),
}

func getServiceURL(key, defaultVal string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultVal
}