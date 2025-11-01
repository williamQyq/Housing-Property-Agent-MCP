package main

import (
	"bff/internal/config"
	"bff/internal/handlers"
	"bff/internal/middleware"
	"bff/internal/services"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/graphql-go/graphql"
	"github.com/graphql-go/handler"
	"github.com/sirupsen/logrus"
)

func main() {
	// Load configuration
	cfg := config.Load()

	// Setup logging
	logrus.SetLevel(logrus.InfoLevel)
	logrus.SetFormatter(&logrus.JSONFormatter{})

	// Initialize services
	identityService := services.NewIdentityService(cfg.IdentityServiceURL)
	orchestratorService := services.NewOrchestratorService(cfg.OrchestratorServiceURL)
	agentService := services.NewAgentService(cfg.AgentServiceURL)

	// Initialize handlers
	authHandler := handlers.NewAuthHandler(identityService)
	roomHandler := handlers.NewRoomHandler(orchestratorService)
	agentHandler := handlers.NewAgentHandler(agentService)

	// Setup Gin router
	router := gin.New()
	router.Use(gin.Logger())
	router.Use(gin.Recovery())
	router.Use(middleware.CORS())

	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	// API routes
	api := router.Group("/api/v1")
	{
		// Auth routes
		auth := api.Group("/auth")
		{
			auth.POST("/otp/start", authHandler.StartOTP)
			auth.POST("/otp/verify", authHandler.VerifyOTP)
			auth.POST("/refresh", authHandler.RefreshToken)
		}

		// Room routes
		rooms := api.Group("/rooms")
		rooms.Use(middleware.AuthRequired())
		{
			rooms.POST("", roomHandler.CreateRoom)
			rooms.GET("", roomHandler.ListRooms)
			rooms.GET("/:id", roomHandler.GetRoom)
			rooms.POST("/:id/invites", roomHandler.CreateInvite)
			rooms.POST("/invites/:token/accept", roomHandler.AcceptInvite)
		}

		// Agent routes
		agent := api.Group("/agent")
		agent.Use(middleware.AuthRequired())
		{
			agent.POST("/execute", agentHandler.ExecuteTool)
		}
	}

	// GraphQL endpoint
	schema := createGraphQLSchema(identityService, orchestratorService, agentService)
	graphqlHandler := handler.New(&handler.Config{
		Schema:   &schema,
		Pretty:   true,
		GraphiQL: true,
	})
	router.POST("/graphql", gin.WrapF(graphqlHandler.ServeHTTP))
	router.GET("/graphql", gin.WrapF(graphqlHandler.ServeHTTP))

	// Start server
	logrus.Infof("Starting BFF server on port %s", cfg.Port)
	if err := router.Run(":" + cfg.Port); err != nil {
		log.Fatal("Failed to start server:", err)
	}
}

func createGraphQLSchema(identityService *services.IdentityService, orchestratorService *services.OrchestratorService, agentService *services.AgentService) graphql.Schema {
	// Define GraphQL types
	userType := graphql.NewObject(graphql.ObjectConfig{
		Name: "User",
		Fields: graphql.Fields{
			"id": &graphql.Field{
				Type: graphql.String,
			},
			"phone": &graphql.Field{
				Type: graphql.String,
			},
			"createdAt": &graphql.Field{
				Type: graphql.String,
			},
		},
	})

	roomType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Room",
		Fields: graphql.Fields{
			"id": &graphql.Field{
				Type: graphql.String,
			},
			"name": &graphql.Field{
				Type: graphql.String,
			},
			"ownerId": &graphql.Field{
				Type: graphql.String,
			},
			"createdAt": &graphql.Field{
				Type: graphql.String,
			},
		},
	})

	// Define root query
	rootQuery := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"user": &graphql.Field{
				Type: userType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
				},
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					// Implementation would call identity service
					return nil, nil
				},
			},
			"rooms": &graphql.Field{
				Type: graphql.NewList(roomType),
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					// Implementation would call orchestrator service
					return nil, nil
				},
			},
		},
	})

	// Define root mutation
	rootMutation := graphql.NewObject(graphql.ObjectConfig{
		Name: "Mutation",
		Fields: graphql.Fields{
			"createRoom": &graphql.Field{
				Type: roomType,
				Args: graphql.FieldConfigArgument{
					"name": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
					"role": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					// Implementation would call orchestrator service
					return nil, nil
				},
			},
		},
	})

	// Create schema
	schema, err := graphql.NewSchema(graphql.SchemaConfig{
		Query:    rootQuery,
		Mutation: rootMutation,
	})
	if err != nil {
		log.Fatal("Failed to create GraphQL schema:", err)
	}

	return schema
}
