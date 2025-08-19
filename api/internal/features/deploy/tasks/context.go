package tasks

import (
	"time"

	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
	"github.com/raghavyuva/nixopus-api/internal/features/logger"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
)

type ContextTask struct {
	TaskService    *TaskService
	ContextConfig  ContextConfig
	UserId         uuid.UUID
	OrganizationId uuid.UUID
}

type ContextConfig struct {
	Deployment  *types.CreateDeploymentRequest
	ContextPath string
}

// GetApplicationData creates an application from a CreateDeploymentRequest
// and a user ID. It populates the application's fields with the corresponding
// values from the request, and sets the CreatedAt and UpdatedAt fields to the
// current time.
// It returns the application data.
func (c *ContextTask) GetApplicationData(
	deployment *types.CreateDeploymentRequest,
	createdAt *time.Time,
) shared_types.Application {

	timeValue := time.Now()
	if createdAt != nil {
		timeValue = *createdAt
	}

	application := shared_types.Application{
		ID:                   uuid.New(),
		Name:                 deployment.Name,
		BuildVariables:       GetStringFromMap(deployment.BuildVariables),
		EnvironmentVariables: GetStringFromMap(deployment.EnvironmentVariables),
		Environment:          deployment.Environment,
		BuildPack:            deployment.BuildPack,
		Repository:           deployment.Repository,
		Branch:               deployment.Branch,
		PreRunCommand:        deployment.PreRunCommand,
		PostRunCommand:       deployment.PostRunCommand,
		Port:                 deployment.Port,
		Domain:               deployment.Domain,
		UserID:               c.UserId,
		CreatedAt:            timeValue,
		UpdatedAt:            time.Now(),
		DockerfilePath:       deployment.DockerfilePath,
		BasePath:             deployment.BasePath,
		OrganizationID:       c.OrganizationId,
	}

	return application
}

// GetDeploymentConfig creates an ApplicationDeployment from an Application.
// It sets the CreatedAt and UpdatedAt fields with the current time and returns
// the created ApplicationDeployment.
// It returns the created ApplicationDeployment.
func (c *ContextTask) GetDeploymentConfig(application shared_types.Application) shared_types.ApplicationDeployment {
	applicationDeployment := shared_types.ApplicationDeployment{
		ID:              uuid.New(),
		ApplicationID:   application.ID,
		CommitHash:      "", // Initialize with an empty string
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
		ContainerID:     "",
		ContainerName:   "",
		ContainerImage:  "",
		ContainerStatus: "",
	}

	return applicationDeployment
}

// PersistApplicationDeploymentData persists the application and application deployment data to the database.
// It returns an error if the operation fails.
func (c *ContextTask) PersistApplicationDeploymentData(application shared_types.Application, applicationDeployment shared_types.ApplicationDeployment) error {
	operations := []struct {
		operation  func() error
		errMessage string
	}{
		{
			operation: func() error {
				return c.TaskService.Storage.AddApplication(&application)
			},
			errMessage: types.LogFailedToCreateApplicationRecord,
		},
		{
			operation: func() error {
				return c.TaskService.Storage.AddApplicationDeployment(&applicationDeployment)
			},
			errMessage: types.LogFailedToCreateApplicationDeployment,
		},
	}

	for _, op := range operations {
		if err := c.executeDBOperations(op.operation, op.errMessage); err != nil {
			return err
		}
	}

	return nil
}

// PersistApplicationDeploymentStatus creates and persists the initial application deployment status.
// It returns the created status record or an error if the operation fails.
func (c *ContextTask) PersistApplicationDeploymentStatus(applicationDeployment shared_types.ApplicationDeployment) (*shared_types.ApplicationDeploymentStatus, error) {
	initialStatus := shared_types.ApplicationDeploymentStatus{
		ID:                      uuid.New(),
		ApplicationDeploymentID: applicationDeployment.ID,
		Status:                  shared_types.Started,
		UpdatedAt:               time.Now(),
	}

	err := c.TaskService.Storage.AddApplicationDeploymentStatus(&initialStatus)
	if err != nil {
		return nil, err
	}

	return &initialStatus, nil
}

// executeDBOperations executes a database operation and logs an error if it fails.
// The first parameter is a function that performs the database operation.
// The second parameter is an error message prefix that is used when logging the error.
// If the operation fails, it logs the error message and returns the error.
// Otherwise, it returns nil.
func (c *ContextTask) executeDBOperations(fn func() error, errMessage string) error {
	err := fn()
	if err != nil {
		c.TaskService.Logger.Log(logger.Error, errMessage+err.Error(), "")
		return err
	}
	return nil
}

// PrepareContext prepares the context for the deployment.
// It returns an error if the operation fails.
func (c *ContextTask) PrepareContext() (shared_types.TaskPayload, error) {
	now := time.Now()
	application := c.GetApplicationData(c.ContextConfig.Deployment, &now)
	applicationDeployment := c.GetDeploymentConfig(application)

	err := c.PersistApplicationDeploymentData(application, applicationDeployment)
	if err != nil {
		return shared_types.TaskPayload{}, err
	}

	// Create initial deployment status
	initialStatus, err := c.PersistApplicationDeploymentStatus(applicationDeployment)
	if err != nil {
		return shared_types.TaskPayload{}, err
	}

	return shared_types.TaskPayload{
		Application:           application,
		ApplicationDeployment: applicationDeployment,
		Status:                initialStatus,
	}, nil
}
