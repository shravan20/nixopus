package tasks

// import (
// 	"github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
// 	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
// )

// func (s *TaskService) BuildPack(d PrepareContextResult) error {
// 	var err error
// 	switch d.Application.BuildPack {
// 	case shared_types.DockerFile:
// 		err = s.handleDockerfileDeployment(d)
// 	case shared_types.DockerCompose:
// 		err = s.handleDockerComposeDeployment(d)
// 	case shared_types.Static:
// 		err = s.handleStaticDeployment(d)
// 	default:
// 		return types.ErrInvalidBuildPack
// 	}

// 	if err != nil {
// 		return err
// 	}
// 	return nil
// }
