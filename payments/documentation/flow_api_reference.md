# Flow API - Documentación de Referencia

## Información General

**Flow** es una plataforma chilena de procesamiento de pagos que ofrece APIs REST para integrar pagos en aplicaciones.

Documentación oficial: https://developers.flow.cl

### URLs de la API

| Entorno | URL Base |
|---------|----------|
| Sandbox (pruebas) | `https://sandbox.flow.cl/api` |
| Producción | `https://www.flow.cl/api` |

### Autenticación

Requiere dos credenciales que se obtienen desde el dashboard de Flow:
- **API Key**: Identificador público del comercio
- **Secret Key**: Clave secreta para firmar las peticiones

Todas las peticiones deben firmarse con **HMAC-SHA256** usando el Secret Key.

---

## Servicios Disponibles

Flow ofrece los siguientes servicios via API:

| Servicio | Descripción |
|----------|-------------|
| Payment | Pagos únicos |
| Customer | Gestión de clientes para cobros recurrentes |
| Cargo Automático | Cobros a tarjetas registradas |
| Subscription | Planes de suscripción con cobros periódicos |
| Refund | Reembolsos |

---

## 1. Payment (Pagos Únicos)

Permite crear órdenes de pago individuales.

### `/payment/create`

Crea una orden de pago y retorna URL + token para redirigir al cliente.

**Parámetros requeridos:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `commerceOrder` | string | Identificador único de la orden en tu sistema |
| `subject` | string | Descripción del pago |
| `currency` | string | Moneda (ej: "CLP") |
| `amount` | int | Monto a pagar |
| `email` | string | Correo del cliente |
| `urlConfirmation` | string | URL webhook para notificación de pago |
| `urlReturn` | string | URL donde redirigir al cliente después del pago |

**Respuesta:**
```json
{
    "url": "https://www.flow.cl/app/pay.php",
    "token": "tok_xxxxxx",
    "flowOrder": 123456
}
```

**URL de pago completa:** `{url}?token={token}`

### `/payment/getStatus`

Obtiene el estado de un pago usando el token.

**Estados posibles:**

| Código | Estado |
|--------|--------|
| 1 | Pendiente |
| 2 | Pagado |
| 3 | Rechazado |
| 4 | Cancelado |

### `/payment/getStatusByFlowOrder`

Similar a getStatus pero usa el flowOrder en lugar del token.

**IMPORTANTE:** Los tokens de `/payment/create` son de **uso único**. Una vez pagado o expirado, no se puede reutilizar.

---

## 2. Customer (Clientes)

Permite registrar clientes para cobros recurrentes.

### `/customer/create`

Crea un cliente en Flow.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `name` | string | Nombre del cliente |
| `email` | string | Correo del cliente |
| `externalId` | string | ID del cliente en tu sistema |

**Respuesta:**
```json
{
    "customerId": "cus_xxxxxx",
    "created": "2025-01-13",
    "email": "cliente@ejemplo.com",
    "name": "Juan Pérez",
    "externalId": "CLI-001"
}
```

### `/customer/register`

Genera URL para que el cliente registre su tarjeta.

**Respuesta:**
```json
{
    "url": "https://www.flow.cl/app/register.php",
    "token": "tok_xxxxxx"
}
```

### `/customer/getRegisterStatus`

Verifica si el cliente completó el registro de su tarjeta.

### `/customer/delete`

Elimina el registro de la tarjeta de un cliente.

---

## 3. Cargo Automático

Permite cobrar a clientes que tienen tarjeta registrada.

### `/customer/charge`

Realiza un cargo automático a la tarjeta del cliente.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `customerId` | string | ID del cliente en Flow |
| `amount` | int | Monto a cobrar |
| `subject` | string | Descripción del cobro |
| `commerceOrder` | string | ID de la orden en tu sistema |

**Límites por defecto:**
- Monto máximo por transacción: 250.000 CLP
- Monto máximo diario por cliente: 500.000 CLP
- Máximo 5 cobros diarios por cliente

### `/customer/collect`

Envía un cobro a un cliente. Si tiene tarjeta registrada, cobra automáticamente. Si no, genera un link de pago.

**Parámetros adicionales:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `byEmail` | int | Si es 1, envía el cobro por email |

### `/customer/batchCollect`

Envía múltiples cobros de forma masiva y asíncrona.

### `/customer/reverseCharge`

Reversa un cargo dentro de las 24 horas siguientes.

---

## 4. Subscription (Suscripciones)

Permite crear planes y suscribir clientes para cobros periódicos automáticos.

### `/plans/create`

Crea un plan de suscripción.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `planId` | string | ID único del plan |
| `name` | string | Nombre del plan |
| `currency` | string | Moneda |
| `amount` | int | Monto del plan |
| `interval` | int | Intervalo de cobro (1=diario, 2=semanal, 3=mensual, 4=anual) |

### `/plans/edit`

Edita un plan existente. Si tiene clientes suscritos, solo puede modificar `trial_period_days`.

### `/plans/delete`

Elimina un plan de suscripción.

### `/subscription/create`

Suscribe un cliente a un plan.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `planId` | string | ID del plan |
| `customerId` | string | ID del cliente |
| `subscription_start` | date | Fecha inicio (opcional) |
| `trial_period_days` | int | Días de prueba (opcional) |

### `/subscription/cancel`

Cancela una suscripción.

---

## 5. Refund (Reembolsos)

### `/refund/create`

Crea un reembolso para una transacción.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `flowOrder` | int | Número de orden de Flow |
| `amount` | int | Monto a reembolsar |
| `receiverEmail` | string | Email del receptor |

---

## Flujos de Pago

### Pago Único

```
1. Tu sistema llama a /payment/create
2. Flow retorna URL + token
3. Redirigir cliente a la URL de pago
4. Cliente paga en Flow
5. Flow envía POST a urlConfirmation con el token
6. Tu sistema llama a /payment/getStatus para verificar
7. Actualizar estado en tu base de datos
8. Cliente es redirigido a urlReturn
```

### Cargo Automático

```
1. Crear cliente con /customer/create
2. Invitar a registrar tarjeta con /customer/register
3. Cliente registra su tarjeta en Flow
4. Verificar registro con /customer/getRegisterStatus
5. Cuando quieras cobrar: /customer/charge
6. Flow procesa el cobro automáticamente
7. Recibir confirmación via webhook
```

### Suscripción

```
1. Crear plan con /plans/create
2. Crear cliente con /customer/create
3. Suscribir cliente con /subscription/create
4. Flow cobra automáticamente según el intervalo del plan
5. Recibir confirmaciones via webhook
```

---

## Webhooks (Notificaciones)

Flow envía notificaciones POST a las URLs configuradas:

- `urlConfirmation`: Cuando un pago es confirmado
- El POST contiene solo el `token`
- Debes llamar a `/payment/getStatus` para obtener los detalles

**IMPORTANTE:** La confirmación puede llegar ANTES de que el cliente sea redirigido a `urlReturn`. Guarda la orden cuando el cliente hace clic en "Pagar", no esperes el redirect.

---

## Botón de Pago (Dashboard)

Además de la API, Flow ofrece "Botón de Pago" desde el dashboard:

- Se crea desde la cuenta Flow sin código
- **SÍ es reutilizable** - múltiples clientes pueden usar el mismo link
- Permite monto fijo o variable (el cliente ingresa el monto)
- Configurable con fecha de vencimiento
- Limitable por stock

**Limitación:** No se controla programáticamente, ideal solo para ventas simples.

---

## Medios de Pago Soportados

- Tarjetas: Visa, MasterCard, American Express
- Webpay (Transbank)
- Transferencias bancarias
- Servipag
- Mach
- Onepay
- Billeteras digitales
- Más de 30 medios de pago disponibles

---

## Comparativa de Métodos de Pago

| Método | Reutilizable | Control Programático | Monto Variable |
|--------|--------------|---------------------|----------------|
| `/payment/create` | ❌ No | ✅ Sí | ✅ Sí |
| Botón de Pago (dashboard) | ✅ Sí | ❌ No | ⚠️ Fijo o libre |
| `/customer/charge` | ✅ Sí | ✅ Sí | ✅ Sí |
| `/subscription/create` | ✅ Sí | ✅ Sí | ❌ Según plan |

---

## Recursos

- Documentación oficial: https://developers.flow.cl
- API Reference: https://developers.flow.cl/en/api
- Librería Python pyflowcl: https://pypi.org/project/pyflowcl/
- GitHub Flow: https://github.com/flowcl
