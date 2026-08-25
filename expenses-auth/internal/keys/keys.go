package keys

import (
	"bytes"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/pem"
	"errors"
	"fmt"
	"os"

	"github.com/lestrrat-go/jwx/v2/jwa"
	"github.com/lestrrat-go/jwx/v2/jwk"
)

type Manager struct {
	privateKey *rsa.PrivateKey
	kid        string
	publicJWKS jwk.Set
}

// LoadOrGenerate reads the RSA private key from keyPath, generating and
// persisting a new one if the file doesn't exist. Intended for local
// development, where there's no secret store to hand the key to the process.
func LoadOrGenerate(keyPath string) (*Manager, error) {
	var privateKey *rsa.PrivateKey

	data, err := os.ReadFile(keyPath)
	if err != nil {
		if !errors.Is(err, os.ErrNotExist) {
			return nil, fmt.Errorf("read key file: %w", err)
		}
		privateKey, err = rsa.GenerateKey(rand.Reader, 2048)
		if err != nil {
			return nil, fmt.Errorf("generate RSA key: %w", err)
		}
		if err := persistKey(keyPath, privateKey); err != nil {
			return nil, fmt.Errorf("persist key: %w", err)
		}
	} else {
		privateKey, err = parsePEM(data)
		if err != nil {
			return nil, fmt.Errorf("parse key file: %w", err)
		}
	}

	return newManager(privateKey)
}

// LoadFromPEM builds a Manager from PEM-encoded key material supplied
// directly (e.g. from a secret-manager-backed env var), with no file access.
// It tolerates literal "\n" sequences in place of real newlines, since some
// deployment platforms flatten multiline env var values.
func LoadFromPEM(pemData []byte) (*Manager, error) {
	privateKey, err := parsePEM(pemData)
	if err != nil {
		return nil, fmt.Errorf("parse key data: %w", err)
	}
	return newManager(privateKey)
}

func parsePEM(data []byte) (*rsa.PrivateKey, error) {
	block, _ := pem.Decode(data)
	if block == nil {
		block, _ = pem.Decode(bytes.ReplaceAll(data, []byte(`\n`), []byte("\n")))
	}
	if block == nil {
		return nil, errors.New("failed to decode PEM block")
	}

	// Traditional PKCS#1 ("RSA PRIVATE KEY", what this package generates) and
	// PKCS#8 ("PRIVATE KEY", the default output of `openssl genrsa`/`genpkey`
	// on OpenSSL 3.x) are both in circulation for externally-supplied keys.
	if key, err := x509.ParsePKCS1PrivateKey(block.Bytes); err == nil {
		return key, nil
	}

	pkcs8Key, err := x509.ParsePKCS8PrivateKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("not a valid PKCS#1 or PKCS#8 RSA key: %w", err)
	}
	rsaKey, ok := pkcs8Key.(*rsa.PrivateKey)
	if !ok {
		return nil, errors.New("key is not an RSA private key")
	}
	return rsaKey, nil
}

func newManager(privateKey *rsa.PrivateKey) (*Manager, error) {
	pubDER, err := x509.MarshalPKIXPublicKey(&privateKey.PublicKey)
	if err != nil {
		return nil, fmt.Errorf("marshal public key: %w", err)
	}
	h := sha256.Sum256(pubDER)
	kid := fmt.Sprintf("%x", h[:8])

	privJWK, err := jwk.FromRaw(privateKey)
	if err != nil {
		return nil, fmt.Errorf("build JWK from private key: %w", err)
	}
	if err := privJWK.Set(jwk.KeyIDKey, kid); err != nil {
		return nil, fmt.Errorf("set kid on private JWK: %w", err)
	}

	pubJWK, err := privJWK.PublicKey()
	if err != nil {
		return nil, fmt.Errorf("extract public JWK: %w", err)
	}
	if err := pubJWK.Set(jwk.AlgorithmKey, jwa.RS256); err != nil {
		return nil, fmt.Errorf("set alg on public JWK: %w", err)
	}

	publicSet := jwk.NewSet()
	if err := publicSet.AddKey(pubJWK); err != nil {
		return nil, fmt.Errorf("add public key to set: %w", err)
	}

	return &Manager{
		privateKey: privateKey,
		kid:        kid,
		publicJWKS: publicSet,
	}, nil
}

func persistKey(path string, key *rsa.PrivateKey) error {
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		return err
	}
	defer f.Close()
	return pem.Encode(f, &pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(key),
	})
}

func (m *Manager) PrivateKey() *rsa.PrivateKey { return m.privateKey }
func (m *Manager) KID() string                 { return m.kid }
func (m *Manager) PublicJWKS() jwk.Set         { return m.publicJWKS }
