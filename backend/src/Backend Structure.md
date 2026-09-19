# Backend Project Structure

This is the recommended modular architecture for the backend project:

```text
backend/
├── src/
│   ├── api/             # Enrutador principal, versiones de la API (v1/, v2/) y configuración de documentación (Swagger/OpenAPI).
│   ├── config/          # Variables de entorno y configuraciones centralizadas.
│   ├── database/        # Cliente del ORM, migraciones y seeders.
│   ├── middleware/      # Interceptores HTTP globales (manejo de errores, CORS, rate limiting).
│   ├── modules/         # El núcleo del proyecto (Arquitectura Modular).
│   │   ├── auth/        
│   │   │   ├── auth.controller.ts  # Rutas específicas del módulo
│   │   │   ├── auth.service.ts     # Lógica de negocio
│   │   │   └── auth.model.ts       # Esquema de base de datos o entidad
│   │   └── users/       
│   ├── services/        # Exclusivo para servicios de infraestructura o externos (ej. S3Service, MailerService, StripeService) que no pertenecen a un dominio específico.
│   └── shared/          # Funciones de ayuda (utils), constantes, enums y tipos TypeScript globales.
└── tests/
    ├── unit/
    └── integration/
```