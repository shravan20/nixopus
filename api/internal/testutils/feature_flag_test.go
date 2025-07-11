package testutils

import (
	"fmt"
	"os"
	"testing"
)

func TestFeatureFlagSetup(t *testing.T) {
	// Test the old way (without all features enabled)
	t.Run("Standard setup", func(t *testing.T) {
		setup := NewTestSetup()
		user, org, err := setup.GetTestAuthResponse()
		if err != nil {
			t.Fatalf("failed to get test auth response: %v", err)
		}

		fmt.Printf("Standard setup - User: %s, Org: %s\n", user.User.Email, org.Name)
	})

	// Test the new way (with all features enabled)
	t.Run("All features enabled setup", func(t *testing.T) {
		setup := NewTestSetup()
		user, org, err := setup.GetTestAuthResponseWithAllFeatures()
		if err != nil {
			t.Fatalf("failed to get test auth response with all features: %v", err)
		}

		fmt.Printf("All features enabled setup - User: %s, Org: %s\n", user.User.Email, org.Name)
	})
}

func TestMain(m *testing.M) {
	os.Exit(m.Run())
}
