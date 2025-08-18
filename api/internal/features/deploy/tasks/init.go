package tasks

import (
	"fmt"

	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
)

func (t *TaskService) CreateDeploymentTask(deployment *types.CreateDeploymentRequest, userID uuid.UUID, organizationID uuid.UUID) error {
	prepareContextTask := PrepareContextTask{
		TaskService: t,
		PrepareContextConfig: PrepareContextConfig{
			Deployment: deployment,
		},
		UserId:         userID,
		OrganizationId: organizationID,
	}

	prepareContextResult, err := prepareContextTask.PrepareContext()
	if err != nil {
		return err
	}

	repoPath, err := t.Clone(CloneConfig{
		PrepareContextResult: prepareContextResult,
		DeploymentType:       string(shared_types.DeploymentTypeCreate),
	})

	if err != nil {
		return err
	}

	_, err = t.BuildImage(BuildConfig{
		PrepareContextResult: prepareContextResult,
		ContextPath:          repoPath,
		Force:                false,
		ForceWithoutCache:    false,
	})

	containerResult, err := t.AtomicUpdateContainer(prepareContextResult)

	if err != nil {
		return err
	}

	fmt.Printf("containerResult: %+v\n", containerResult)

	return nil
}

// TODO :
// PRE RUN POST RUN COMMANDS EXECUTION	
// REVERSE PROXY CONFIGURATION
// Updating the application deployment data and application data found out during the different stages of the tasks
// Logger of the tasks (add log function to the task service)
// Update the statuses during the different stages of the tasks