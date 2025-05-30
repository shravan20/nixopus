package controller

import (
	"net/http"

	"github.com/go-fuego/fuego"
	"github.com/raghavyuva/nixopus-api/internal/features/logger"
	"github.com/raghavyuva/nixopus-api/internal/features/notification"
	"github.com/raghavyuva/nixopus-api/internal/utils"

	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
)

func (c *NotificationController) AddSmtp(f fuego.ContextWithBody[notification.CreateSMTPConfigRequest]) (*shared_types.Response, error) {
	w, r := f.Response(), f.Request()

	var SMTPConfigs notification.CreateSMTPConfigRequest
	if !c.parseAndValidate(w, r, &SMTPConfigs) {
		return nil, fuego.HTTPError{
			Err:    nil,
			Status: http.StatusBadRequest,
		}
	}

	user := utils.GetUser(w, r)
	if user == nil {
		c.logger.Log(logger.Error, "User authentication failed", "")
		return nil, fuego.HTTPError{
			Err:    nil,
			Status: http.StatusUnauthorized,
		}
	}

	err := c.service.AddSmtp(SMTPConfigs, user.ID)
	if err != nil {
		c.logger.Log(logger.Error, "Failed to add SMTP config", err.Error())
		return nil, fuego.HTTPError{
			Err:    err,
			Status: http.StatusInternalServerError,
		}
	}

	return &shared_types.Response{
		Status:  "success",
		Message: "SMTP Config added successfully",
		Data:    nil,
	}, nil
}
