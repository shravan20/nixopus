package controller

import (
	"fmt"
	"strings"

	"github.com/raghavyuva/nixopus-api/internal/features/logger"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
)

func (c *ContainerController) isProtectedContainer(containerID string, action string) (*shared_types.Response, bool) {
	details, err := c.dockerService.GetContainerById(containerID)
	if err != nil {
		return nil, false
	}
	name := strings.ToLower(details.Name)
	if strings.Contains(name, "nixopus") {
		c.logger.Log(logger.Info, fmt.Sprintf("Skipping %s for protected container", action), details.Name)
		return &shared_types.Response{
			Status:  "success",
			Message: "Operation skipped for protected container",
			Data:    map[string]string{"status": "skipped"},
		}, true
	}
	return nil, false
}
