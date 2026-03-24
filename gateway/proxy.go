package main

import (
	"crypto/tls"    // TLS certificates handle karne ke liye & Gateway ka certificate load karna
	"crypto/x509"   // X.509 certificate format & CA certificate pool banana
	"fmt"
	"net/http"      //http client bnana
	"net/http/httputil"  //req forward ke liye,  reverse proxy bnana
	"net/url"            //url parse krne ke liye
	"os"
	"strings"
	"log"
)

//gateway ka certificate request ke sath yhi bhejta hai -- global rkha hai taki baar baar use ho skte wrna hr baar cert load krna pdta
var mtlsClient *http.Client

func initMTLS() {
	cert, err := tls.LoadX509KeyPair(
		"/certs/gateway.crt",   //gateway ka public cert
		"/certs/gateway.key",   //gateway ki private key
	)

	//Agar certificate na mile toh
	if err != nil {
       log.Fatal("FATAL: Gateway cert nahi mila:", err)
       // System should NOT start without mTLS in Zero Trust
    }

	caCert, err := os.ReadFile("/certs/ca.crt")  //CA ka cert disk se padha
	if err != nil {
		log.Fatal("FATAL: CA cert nahi mila:", err)
	}

	caCertPool := x509.NewCertPool()   //cert ka pool bna diya
	caCertPool.AppendCertsFromPEM(caCert)   //usme CA cert daal diya, production me multiple CAs ho skte hai isliye pool bna lo ki inki sign hue certs ko accept krna

	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},   //gateway apna cert bhejega
		RootCAs:      caCertPool,                //sirf pool ke CAs ka trusted hoga
		InsecureSkipVerify: false,               // Certificate verify karo
	}

	transport := &http.Transport{      
		TLSClientConfig: tlsConfig,  //mTLS config lagao
		DialTLSContext: nil,         //Default dialer use kro
	}
	//Normal HTTP Client → Plain connections
    // mTLS Transport    → Har connection pe:
    //                     1. Certificate exchange
    //                     2. Encryption setup
    //                     3. Phir data transfer

	mtlsClient = &http.Client{Transport: transport}
	fmt.Println("mTLS initialized!")
}

func forwardRequest(w http.ResponseWriter, r *http.Request, claims *Claims) {
    
	//shi service dhundo
	basePath := getBasePath(r.URL.Path)

	targetURL, exists := Services[basePath]
	if !exists {                       //service nhi mili to
		sendError(w, http.StatusNotFound,
			fmt.Sprintf("Service '%s' nahi mili", basePath),
			"routing")
		return
	}
    
	//url ko pare krna pdega because httputil.NewSingleHostReverseProxy() ko url object chaiye string nhi
	//url.Parse → string ko URL struct mein convert
	target, err := url.Parse(targetURL)
	if err != nil {
		sendError(w, http.StatusInternalServerError, "Routing error", "proxy")
		return
	}

	// mTLS proxy — apna certificate saath bhejega
	proxy := httputil.NewSingleHostReverseProxy(target)   //ye built-in reverse proxy request ko forward krta hai
	proxy.Transport = mtlsClient.Transport  //hum mtls Transport use kr rhe hai matlab hr req me gateway apna cert bhej rha hai, normal to ye plain http use krta
    

	//services khud auth nhi krti, gateway kr chuka hai ye btatai hai mai ramesh hu, hr role hai tum directly serve krdo
	r.Header.Set("X-User-Email", claims.Email)
	r.Header.Set("X-User-Role", claims.Role)
	r.Header.Set("X-Forwarded-By", "ZTNA-Gateway")

	fmt.Printf("📨 mTLS Forward: %s → %s (User: %s)\n",
		r.URL.Path, targetURL, claims.Email)

	proxy.ServeHTTP(w, r)
}

func getBasePath(path string) string {
	parts := strings.Split(path, "/")
	if len(parts) >= 2 {
		return "/" + parts[1]
	}
	return path

// 	User request kar sakta hai:
// /hr-portal              → /hr-portal 
// /hr-portal/dashboard    → /hr-portal 
// /hr-portal/user/123     → /hr-portal 

// Services map mein sirf /hr-portal hai  for simplicity
// Isliye pehla part nikala

}
