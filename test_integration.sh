#!/bin/bash

# Script de pruebas rápidas de integración con curl
# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
ADMIN_APPS_URL="http://127.0.0.1:8000"
USERNAME="felipe@comtech.local"
PASSWORD="F3l1p32191"
API_KEY="isosmart-integration-key-2025"
ISO_BASE_URL="http://127.0.0.1"
ISO_PORTS=(8001)
ISO_USERNAME="$USERNAME"
ISO_PASSWORD="$PASSWORD"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   PRUEBAS DE INTEGRACIÓN ISO SMART    ${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Test 1: Health Check Admin Apps
echo -e "${YELLOW}[TEST 1] Health Check - Admin Apps${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$ADMIN_APPS_URL/api/health/" 2>&1)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Admin Apps está en línea${NC}"
    echo -e "  Response: $BODY"
else
    echo -e "${RED}✗ Admin Apps no responde (HTTP $HTTP_CODE)${NC}"
    echo -e "  Error: $BODY"
fi
echo ""

# Test 2: Health Check Integracion (API Key)
echo -e "${YELLOW}[TEST 2] Health Check - Integracion${NC}"
INTEGRATION_RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$ADMIN_APPS_URL/api/integration/health/" \
    -H "X-API-Key: $API_KEY" 2>&1)

HTTP_CODE=$(echo "$INTEGRATION_RESPONSE" | tail -n1)
BODY=$(echo "$INTEGRATION_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Integracion OK${NC}"
    echo -e "  Response: $BODY"
else
    echo -e "${RED}✗ Integracion fallo (HTTP $HTTP_CODE)${NC}"
    echo -e "  Error: $BODY"
fi
echo ""

# Test 3: Login y obtener token
echo -e "${YELLOW}[TEST 3] Autenticación JWT${NC}"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    "$ADMIN_APPS_URL/api/auth/login/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" 2>&1)

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
BODY=$(echo "$LOGIN_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Autenticación exitosa${NC}"
    TOKEN=$(echo "$BODY" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
    echo -e "  Token: ${TOKEN:0:50}..."
    
    # Test 4: Listar organizaciones
    echo ""
    echo -e "${YELLOW}[TEST 4] Listar Organizaciones${NC}"
    ORG_RESPONSE=$(curl -s -w "\n%{http_code}" \
        "$ADMIN_APPS_URL/api/organizations/" \
        -H "Authorization: Bearer $TOKEN" 2>&1)
    
    HTTP_CODE=$(echo "$ORG_RESPONSE" | tail -n1)
    BODY=$(echo "$ORG_RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Organizaciones obtenidas${NC}"
        echo -e "  Response: $BODY" | head -c 200
        echo "..."
    else
        echo -e "${RED}✗ Error al obtener organizaciones (HTTP $HTTP_CODE)${NC}"
    fi
    
    # Test 5: Listar usuarios
    echo ""
    echo -e "${YELLOW}[TEST 5] Listar Usuarios${NC}"
    USER_RESPONSE=$(curl -s -w "\n%{http_code}" \
        "$ADMIN_APPS_URL/api/auth/users/" \
        -H "Authorization: Bearer $TOKEN" 2>&1)
    
    HTTP_CODE=$(echo "$USER_RESPONSE" | tail -n1)
    BODY=$(echo "$USER_RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Usuarios obtenidos${NC}"
        echo -e "  Response: $BODY" | head -c 200
        echo "..."
    else
        echo -e "${RED}✗ Error al obtener usuarios (HTTP $HTTP_CODE)${NC}"
    fi
    
    # Test 6: Login ISO Smart y obtener token
    echo ""
    echo -e "${YELLOW}[TEST 6] Autenticación ISO Smart${NC}"
    ISO_LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        "$ISO_BASE_URL:${ISO_PORTS[0]}/api/auth/login/" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$ISO_USERNAME\",\"password\":\"$ISO_PASSWORD\"}" 2>&1)

    ISO_HTTP_CODE=$(echo "$ISO_LOGIN_RESPONSE" | tail -n1)
    ISO_BODY=$(echo "$ISO_LOGIN_RESPONSE" | head -n-1)

    if [ "$ISO_HTTP_CODE" = "200" ]; then
        ISO_TOKEN=$(echo "$ISO_BODY" | grep -o '"access":"[^" ]*' | cut -d'"' -f4)
        echo -e "${GREEN}✓ ISO Smart autenticación exitosa${NC}"
        echo -e "  Token: ${ISO_TOKEN:0:50}..."
    else
        echo -e "${RED}✗ ISO Smart login falló (HTTP $ISO_HTTP_CODE)${NC}"
        echo -e "  Response: $ISO_BODY"
        ISO_TOKEN=""
    fi

    # Test 7: Obtener perfil desde ISO Smart
    echo ""
    echo -e "${YELLOW}[TEST 7] Perfil ISO Smart (/api/auth/me/)${NC}"

    if [ -z "$ISO_TOKEN" ]; then
        echo -e "${RED}✗ Sin token ISO Smart, se omiten pruebas de ISO Smart${NC}"
    else
        ISO_ME_RESPONSE=$(curl -s -w "\n%{http_code}" \
            "$ISO_BASE_URL:${ISO_PORTS[0]}/api/auth/me/" \
            -H "Authorization: Bearer $ISO_TOKEN" 2>&1)

        ISO_HTTP_CODE=$(echo "$ISO_ME_RESPONSE" | tail -n1)
        ISO_BODY=$(echo "$ISO_ME_RESPONSE" | head -n-1)

        if [ "$ISO_HTTP_CODE" = "200" ]; then
            echo -e "${GREEN}✓ Perfil ISO Smart obtenido${NC}"
            echo -e "  Response: $ISO_BODY" | head -c 200
            echo "..."
        else
            echo -e "${RED}✗ Error al obtener perfil ISO Smart (HTTP $ISO_HTTP_CODE)${NC}"
            echo -e "  Error: $ISO_BODY"
        fi

        # Test 8: Listar usuarios ISO Smart
        echo ""
        echo -e "${YELLOW}[TEST 8] Listar usuarios ISO Smart${NC}"
        ISO_USERS_RESPONSE=$(curl -s -w "\n%{http_code}" \
            "$ISO_BASE_URL:${ISO_PORTS[0]}/api/auth/users/" \
            -H "Authorization: Bearer $ISO_TOKEN" 2>&1)

        ISO_HTTP_CODE=$(echo "$ISO_USERS_RESPONSE" | tail -n1)
        ISO_BODY=$(echo "$ISO_USERS_RESPONSE" | head -n-1)

        if [ "$ISO_HTTP_CODE" = "200" ]; then
            echo -e "${GREEN}✓ Usuarios ISO Smart obtenidos${NC}"
            echo -e "  Response: $ISO_BODY" | head -c 200
            echo "..."
        else
            echo -e "${RED}✗ Error al obtener usuarios ISO Smart (HTTP $ISO_HTTP_CODE)${NC}"
            echo -e "  Error: $ISO_BODY"
        fi

        # Test 9: Probar endpoints de ISO Smart
        echo ""
        echo -e "${YELLOW}[TEST 9] Conexión con módulos ISO Smart${NC}"

        for PORT in "${ISO_PORTS[@]}"; do
            ISO_RESPONSE=$(curl -s -w "\n%{http_code}" --connect-timeout 2 \
                "$ISO_BASE_URL:$PORT/api/health/" \
                -H "Authorization: Bearer $ISO_TOKEN" 2>&1)

            HTTP_CODE=$(echo "$ISO_RESPONSE" | tail -n1)
            BODY=$(echo "$ISO_RESPONSE" | head -n-1)

            if [ "$HTTP_CODE" = "200" ]; then
                echo -e "${GREEN}✓ Módulo ISO Smart respondió en puerto $PORT${NC}"
                echo -e "  Response: $BODY"
            else
                echo -e "${RED}✗ Sin respuesta en puerto $PORT (HTTP $HTTP_CODE)${NC}"
                if [ -n "$BODY" ]; then
                    echo -e "  Error: $BODY"
                fi
            fi
        done
    fi
    
else
    echo -e "${RED}✗ Login falló (HTTP $HTTP_CODE)${NC}"
    echo -e "  Response: $BODY"
    echo -e "  Credenciales usadas: $USERNAME / $PASSWORD"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   FIN DE PRUEBAS                      ${NC}"
echo -e "${BLUE}========================================${NC}"
