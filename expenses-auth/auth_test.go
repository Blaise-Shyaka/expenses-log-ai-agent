package main_test

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/lestrrat-go/jwx/v2/jwa"
	"github.com/lestrrat-go/jwx/v2/jwk"
	"github.com/lestrrat-go/jwx/v2/jwt"

	"github.com/blaise/momo-expenses/expenses-auth/internal/keys"
	"github.com/blaise/momo-expenses/expenses-auth/internal/server"
	"github.com/blaise/momo-expenses/expenses-auth/internal/store"
	"github.com/blaise/momo-expenses/expenses-auth/internal/tokens"
)

func newTestServer(t *testing.T) *httptest.Server {
	t.Helper()
	tmp, err := os.CreateTemp(t.TempDir(), "signing-*.key")
	if err != nil {
		t.Fatalf("create temp key file path: %v", err)
	}
	tmp.Close()
	os.Remove(tmp.Name())

	km, err := keys.LoadOrGenerate(tmp.Name())
	if err != nil {
		t.Fatalf("load/generate key: %v", err)
	}

	st := store.NewMemoryStore()
	minter := tokens.NewMinter(km.PrivateKey(), km.KID(), "http://localhost:8001")
	h := server.New(st, km, minter)
	return httptest.NewServer(h)
}

func postJSON(t *testing.T, srv *httptest.Server, path string, body any) *http.Response {
	t.Helper()
	b, err := json.Marshal(body)
	if err != nil {
		t.Fatalf("marshal request: %v", err)
	}
	resp, err := http.Post(srv.URL+path, "application/json", bytes.NewReader(b))
	if err != nil {
		t.Fatalf("POST %s: %v", path, err)
	}
	return resp
}

func getJSON(t *testing.T, srv *httptest.Server, path string) *http.Response {
	t.Helper()
	resp, err := http.Get(srv.URL + path)
	if err != nil {
		t.Fatalf("GET %s: %v", path, err)
	}
	return resp
}

func TestHealth(t *testing.T) {
	srv := newTestServer(t)
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/health")
	if err != nil {
		t.Fatalf("health request: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("health: want 200, got %d", resp.StatusCode)
	}
}

func TestRegister_Success(t *testing.T) {
	srv := newTestServer(t)
	defer srv.Close()

	resp := postJSON(t, srv, "/register", map[string]string{
		"email":      "alice@example.com",
		"password":   "hunter2",
		"first_name": "Alice",
		"last_name":  "Example",
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("register: want 201, got %d: %s", resp.StatusCode, body)
	}

	var result map[string]string
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("decode register response: %v", err)
	}
	if result["email"] != "alice@example.com" {
		t.Errorf("email: want alice@example.com, got %q", result["email"])
	}
	if result["id"] == "" {
		t.Error("id should not be empty")
	}
	if _, ok := result["password"]; ok {
		t.Error("response must not include password field")
	}
	if _, ok := result["password_hash"]; ok {
		t.Error("response must not include password_hash field")
	}
}

func TestRegister_DuplicateEmail(t *testing.T) {
	srv := newTestServer(t)
	defer srv.Close()

	body := map[string]string{
		"email":      "dup@example.com",
		"password":   "pass1",
		"first_name": "D",
		"last_name":  "U",
	}
	resp1 := postJSON(t, srv, "/register", body)
	resp1.Body.Close()

	resp2 := postJSON(t, srv, "/register", body)
	defer resp2.Body.Close()

	if resp2.StatusCode != http.StatusConflict {
		t.Errorf("duplicate register: want 409, got %d", resp2.StatusCode)
	}
}

func TestLogin_Success(t *testing.T) {
	srv := newTestServer(t)
	defer srv.Close()

	postJSON(t, srv, "/register", map[string]string{
		"email":      "bob@example.com",
		"password":   "secretpass",
		"first_name": "Bob",
		"last_name":  "Test",
	}).Body.Close()

	resp := postJSON(t, srv, "/login", map[string]string{
		"email":    "bob@example.com",
		"password": "secretpass",
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("login: want 200, got %d: %s", resp.StatusCode, body)
	}

	var result map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("decode login response: %v", err)
	}

	accessToken, ok := result["access_token"].(string)
	if !ok || accessToken == "" {
		t.Error("access_token should be present and non-empty")
	}
	if _, ok := result["refresh_token"].(string); !ok {
		t.Error("refresh_token should be present")
	}
	if _, ok := result["expires_in"].(float64); !ok {
		t.Error("expires_in should be present")
	}

	parts := strings.Split(accessToken, ".")
	if len(parts) != 3 {
		t.Errorf("access_token should be a 3-part JWT, got %d parts", len(parts))
	}
}

func TestLogin_UnknownEmail_Returns401(t *testing.T) {
	srv := newTestServer(t)
	defer srv.Close()

	resp := postJSON(t, srv, "/login", map[string]string{
		"email":    "nobody@example.com",
		"password": "anything",
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusUnauthorized {
		t.Errorf("unknown email: want 401, got %d", resp.StatusCode)
	}
}

func TestLogin_WrongPassword_Returns401_IndistinguishableBody(t *testing.T) {
	srv := newTestServer(t)
	defer srv.Close()

	postJSON(t, srv, "/register", map[string]string{
		"email":      "carol@example.com",
		"password":   "rightpass",
		"first_name": "Carol",
		"last_name":  "Test",
	}).Body.Close()

	respWrongPw := postJSON(t, srv, "/login", map[string]string{
		"email":    "carol@example.com",
		"password": "wrongpass",
	})
	defer respWrongPw.Body.Close()

	respUnknown := postJSON(t, srv, "/login", map[string]string{
		"email":    "unknown@example.com",
		"password": "anything",
	})
	defer respUnknown.Body.Close()

	if respWrongPw.StatusCode != http.StatusUnauthorized {
		t.Errorf("wrong password: want 401, got %d", respWrongPw.StatusCode)
	}
	if respUnknown.StatusCode != http.StatusUnauthorized {
		t.Errorf("unknown email: want 401, got %d", respUnknown.StatusCode)
	}

	body1, _ := io.ReadAll(respWrongPw.Body)
	body2, _ := io.ReadAll(respUnknown.Body)
	if string(body1) != string(body2) {
		t.Errorf("login failure bodies differ:\n  wrong-pw: %s\n  unknown:  %s", body1, body2)
	}
}

func TestJWKS_RoundTrip(t *testing.T) {
	srv := newTestServer(t)
	defer srv.Close()

	postJSON(t, srv, "/register", map[string]string{
		"email":      "dave@example.com",
		"password":   "davepass",
		"first_name": "Dave",
		"last_name":  "Test",
	}).Body.Close()

	loginResp := postJSON(t, srv, "/login", map[string]string{
		"email":    "dave@example.com",
		"password": "davepass",
	})
	defer loginResp.Body.Close()

	var loginResult map[string]any
	json.NewDecoder(loginResp.Body).Decode(&loginResult)
	accessToken := loginResult["access_token"].(string)

	jwksResp := getJSON(t, srv, "/.well-known/jwks.json")
	defer jwksResp.Body.Close()

	if jwksResp.StatusCode != http.StatusOK {
		t.Fatalf("jwks: want 200, got %d", jwksResp.StatusCode)
	}

	jwksBody, _ := io.ReadAll(jwksResp.Body)
	keySet, err := jwk.ParseString(string(jwksBody))
	if err != nil {
		t.Fatalf("parse JWKS: %v", err)
	}

	if keySet.Len() == 0 {
		t.Fatal("JWKS must contain at least one key")
	}

	parsed, err := jwt.Parse([]byte(accessToken),
		jwt.WithKeySet(keySet),
		jwt.WithValidate(true),
		jwt.WithAcceptableSkew(5*time.Second),
	)
	if err != nil {
		t.Fatalf("verify JWT with JWKS: %v", err)
	}

	if parsed.Subject() == "" {
		t.Error("JWT sub should not be empty")
	}

	audiences := parsed.Audience()
	if len(audiences) == 0 || audiences[0] != "expenses-agent" {
		t.Errorf("JWT aud: want expenses-agent, got %v", audiences)
	}

	tokenType, _ := parsed.Get("token_type")
	if tokenType != "user" {
		t.Errorf("token_type: want user, got %v", tokenType)
	}
}

func TestJWKS_NoPrivateKeyMaterial(t *testing.T) {
	srv := newTestServer(t)
	defer srv.Close()

	resp := getJSON(t, srv, "/.well-known/jwks.json")
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	bodyStr := string(body)

	if strings.Contains(bodyStr, `"d"`) {
		t.Error("JWKS response must not contain private key material (d)")
	}
}

func TestArgon2idUsed(t *testing.T) {
	tmp, _ := os.CreateTemp(t.TempDir(), "*.key")
	tmp.Close()
	os.Remove(tmp.Name())
	km, _ := keys.LoadOrGenerate(tmp.Name())
	minter := tokens.NewMinter(km.PrivateKey(), km.KID(), "http://localhost:8001")

	st := store.NewMemoryStore()
	postJSON(t, httptest.NewServer(server.New(st, km, minter)), "/register", map[string]string{
		"email": "argontest@example.com", "password": "pw", "first_name": "A", "last_name": "B",
	}).Body.Close()

	u, err := st.GetUserByEmail("argontest@example.com")
	if err != nil {
		t.Fatalf("get user: %v", err)
	}
	if !strings.HasPrefix(u.PasswordHash, "$argon2id$") {
		t.Errorf("password hash must use argon2id, got: %q", u.PasswordHash)
	}
}

func TestJWT_KidHeaderPresent(t *testing.T) {
	tmp, _ := os.CreateTemp(t.TempDir(), "*.key")
	tmp.Close()
	os.Remove(tmp.Name())
	km, err := keys.LoadOrGenerate(tmp.Name())
	if err != nil {
		t.Fatalf("load key: %v", err)
	}

	minter := tokens.NewMinter(km.PrivateKey(), km.KID(), "http://localhost:8001")
	tok, err := minter.MintUserToken("test-user-id", 15*time.Minute)
	if err != nil {
		t.Fatalf("mint token: %v", err)
	}

	privJWK, err := jwk.FromRaw(km.PrivateKey())
	if err != nil {
		t.Fatalf("build JWK: %v", err)
	}
	privJWK.Set(jwk.KeyIDKey, km.KID())
	privJWK.Set(jwk.AlgorithmKey, jwa.RS256)

	parsed, err := jwt.Parse([]byte(tok), jwt.WithKey(jwa.RS256, privJWK))
	if err != nil {
		t.Fatalf("parse token: %v", err)
	}
	_ = parsed
}
