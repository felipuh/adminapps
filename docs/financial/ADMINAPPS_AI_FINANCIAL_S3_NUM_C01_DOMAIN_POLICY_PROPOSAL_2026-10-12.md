# ADMINAPPS — S3-IMP-01 / NUM-C01 Domain Policy Proposal

Preparado el **2026-10-12**. Ficha para decisión humana; no aprueba, implementa
ni activa la política.

Base contractual: [contract freeze del 2026-10-12](./ADMINAPPS_AI_FINANCIAL_S3_IMP_01_CONTRACT_FREEZE_HUMAN_DECISION_2026-10-12.md)
y [Human Architecture Adjudication Gate](./ADMINAPPS_AI_FINANCIAL_S3_HUMAN_ARCHITECTURE_ADJUDICATION_GATE_2026-10-12.md).

## A. Executive Verdict

**Recomendación:** presentar para ratificación el perfil
`S3-CONTROLLED-TEST-CAPACITY-V1`, con `L_R=64` caracteres ASCII por
`request_class`, `L_E=256` bytes ASCII por `evidence_id`, `N_E=32` referencias
por solicitud y `B_M=9169` bytes derivados.

La comprobación offline con Python stdlib pasó: el material sintético de nueve
campos y assertion tenant completo de cuatro campos serializa a exactamente
9169 bytes bajo las reglas documentadas. Esta comprobación acredita la aritmética
y la forma del vector sintético; no mide límites legítimos de consumidores ni
demuestra capacidad operacional.

Las cifras son **propuestas nuevas de política**, no requisitos contractuales,
límites encontrados en código ni máximos derivados de un inventario de
consumidores. Por ello, la decisión permanece:

- `NUM-C01 = PENDING_HUMAN_APPROVAL`
- `S3-IMP-01 = BLOCKED_PENDING_AUTHORITY`
- `S3_DECISION_02A_NOT_CLOSED`
- `PHASE31_5 = EXECUTION_HELD`

No se cambia el comportamiento del producto ni se inicia implementación.

## B. Candidate Numerical Limits

| Parámetro | Candidato | Interpretación propuesta |
| --- | ---: | --- |
| `L_R` | 64 | Longitud máxima de `request_class`, caracteres ASCII |
| `L_E` | 256 | Longitud máxima de cada `evidence_id`, bytes ASCII |
| `N_E` | 32 | Número máximo de referencias `evidence_ids` por solicitud |
| `B_M` | 9169 | Longitud máxima derivada del material JSON canónico, bytes |

Derivación:

```text
B_M = 818 + L_R + (N_E × (L_E + 3) - 1)
    = 818 + 64 + (32 × (256 + 3) - 1)
    = 9169 bytes
```

ASCII hace que caracteres y bytes coincidan para las dos cadenas bajo este
perfil. No es una equivalencia general: una cadena no ASCII puede tener más
bytes UTF-8 que caracteres y no satisface la gramática ASCII propuesta.

Los cuatro candidatos aplican simultáneamente como cotas, sin truncamiento,
recorte, coerción, deduplicación ni sustitución por valores predeterminados.
Su adopción requiere aceptación humana expresa.

## C. Offline Validation

Se ejecutó únicamente Python stdlib, sin módulos del producto, Django, bases de
datos, IPC ni servicios. El objeto sintético tuvo el esquema cerrado de nueve
campos y `tenant_assertion` con sus cuatro campos. En un mismo vector se
maximizaron `request_class`, la cantidad y longitud de las referencias, además
de los restantes campos conforme a los máximos de representación descritos en
el contrato freeze.

Resultado:

- `json.dumps(..., sort_keys=True, separators=(',', ':'), ensure_ascii=True,
  allow_nan=False).encode('utf-8')` produjo **9169 bytes**; `ensure_ascii=True`
  se verificó explícitamente.
- La estructura tuvo nueve campos y assertion de cuatro campos.
- Las 32 referencias de 256 caracteres ASCII se conservaron completas y en
  orden lexicográfico tras ordenar; dos identificadores repetidos permanecieron
  dos veces. No hubo truncamiento ni deduplicación.
- SHA-256 se calculó directamente sobre esos bytes canónicos, en lowercase y
  sin dominio, sal ni transformación adicional. Digest del vector sintético:
  `9f466f58842e5a90e16fdfaf520326beb60c267672c9dd7f3e34de4e8462bcb7`.
  Es un resultado de la muestra de esta ficha, no un hash histórico o una
  prueba de equivalencia con un fixture firmado existente.
- El caso de unidad no ASCII `é` tuvo un carácter y dos bytes UTF-8; se confirmó
  que no pertenece al perfil ASCII.
- La base fija del mismo material con clase vacía y lista vacía midió 818 bytes,
  concordante con la constante de la fórmula.

Fronteras para una futura implementación, **solo si el perfil se aprueba**:

| Entrada | Aceptación propuesta | Rechazo propuesto |
| --- | --- | --- |
| `request_class` | 1 y 64 caracteres ASCII | Vacío y 65 |
| Cada `evidence_id` | 1 y 256 bytes ASCII | Vacío y 257 |
| Cantidad de `evidence_ids` | 0 y 32 | 33 |
| Material completo | 9169 bytes | Más de 9169 bytes |

El script comprobó la fórmula, la longitud real del vector máximo, la forma del
objeto, orden, multiplicidad, ausencia de truncamiento y distinción de unidades.
No ejecutó un validador de producto ni una matriz completa de rechazo en sus
fronteras; esos casos corresponden a pruebas sucesoras offline posteriores a
una autorización de implementación.

## D. Compatibility Analysis

El perfil candidato no añade ni elimina claims: conserva las 18 claves firmadas
documentadas en el freeze. Mantiene Ed25519, el dominio y la versión firmados,
la construcción de `M(C)` y el material canónico. No cambia el hash SHA-256 de
un material válido representado por los mismos bytes. `evidence_ids` permanece
ordenado para el hash y conserva identificadores repetidos; no se deduplican
referencias. No se modifican fixtures históricos ni se incorpora fallback al
parser anterior.

La compatibilidad es una conclusión documental/estructural; la validación de
esta ficha no importó código ni comparó un vector real firmado del emisor.
El contrato freeze identifica incompatibilidades que deberán conservarse y
resolverse expresamente: el fixture histórico del executor con assertion
abreviado no satisface el assertion de cuatro campos; y un caso histórico de
sustitución de UUID podría fallar antes con otra categoría de error bajo el
esquema estricto. No se corrigen ni se reescriben aquí esos fixtures u
expectativas.

El rechazo futuro de entradas por encima de los candidatos estrecha la
aceptación y es un cambio de política deliberado; no debe aplicarse antes de
aprobación y autorización de implementación. No se reivindica compatibilidad
de productores externos no inventariados.

## E. Controlled-Test Scope

**Nombre:** `S3-CONTROLLED-TEST-CAPACITY-V1`.

**Alcance exclusivo:** AdminApps; entorno `controlled_test`; datos y fixtures
sintéticos; validación offline; preparación futura de S3-IMP-01.

**Exclusiones:** staging operativo; producción; operaciones financieras reales;
integración operacional ISO Smart o MedSupplier; productores externos no
inventariados; PostgreSQL o servicios IPC reales; activación de S4–S6.

Si, y solo si, el perfil es aprobado y luego implementado bajo autorización
separada, se rechazarán entradas superiores a sus límites. Esta propuesta no
activa rechazos en el producto actual ni autoriza pruebas de runtime.

## F. Risks and Limitations

- No se dispone aquí de máximos legítimos declarados por cada consumidor ni de
  evidencia de que las cifras candidatas cubran todo el dominio. La inspección
  citada por el freeze es estática y no acredita productores desplegados o
  externos.
- El inventario/medición NUM-C01 previo no está disponible como corpus,
  distribución o máximos declarados en el contexto de esta ficha. No se atribuye
  a esos resultados evidencia no visible ni se presenta el vector sintético
  como sustituto.
- Los límites de serialización no demuestran presupuesto de memoria, latencia,
  factibilidad SQL ni suficiencia operacional.
- Consumidores válidos con `request_class` superior a 64, `evidence_id`
  superior a 256 o más de 32 referencias serían rechazados bajo la futura
  política; sin inventario completo no se conoce esa exposición.
- `B_M` depende de los campos fijos y reglas del material en el freeze. Cualquier
  cambio de esquema, gramática o serialización requiere revisar la derivación y
  autoridad antes de reutilizar esta cifra.

## G. Proposed Human Decision

**Decisión única NUM-C01:** adoptar, modificar o rechazar
`S3-CONTROLLED-TEST-CAPACITY-V1` y los cuatro límites de la sección B para el
alcance de la sección E.

1. **Opción recomendada:** adoptar los candidatos únicamente para el alcance
   controlado y sintético definido en esta ficha.
2. **Valores:** `L_R=64`, `L_E=256`, `N_E=32`, `B_M=9169`.
3. **Justificación técnica:** cota finita, verificable y probada en una
   serialización sintética máxima; `B_M` es derivado, no elegido
   independientemente.
4. **Evidencia disponible:** fórmula del contrato freeze, esquema de nueve
   campos/assertion de cuatro campos, inspección documental del contrato y
   comprobación Python stdlib registrada en C. No hay medición de dominio de
   consumidores adjunta.
5. **Limitaciones de dominio:** solo el perfil y alcance de E; no representa un
   máximo operacional ni autoriza consumidores fuera de inventario.
6. **Alcance de aplicación:** únicamente tras aceptación humana y autorización
   de implementación posterior; fuera de eso no hay efecto en el producto.
7. **Riesgos residuales:** cobertura incompleta de consumidores y posible
   rechazo de entradas legítimas mayores; presupuesto de ejecución no medido.
8. **Autoridades funcionales requeridas:** responsable del contrato financiero
   (F) y responsable de seguridad/protocolo (S), con mandato acreditado; los
   dueños de los consumidores incluidos deben declarar y aceptar sus máximos
   legítimos. La autoridad de gobierno verifica mandato, acta y alcance.
9. **Campos pendientes de aprobación:** opción final; límites confirmados o
   modificados y `B_M` recalculado; evidencia/corpus y cobertura de consumidores;
   aceptación de riesgos y exclusiones; identidad, función y mandato de
   firmantes; acta/procedencia, fecha efectiva y zona horaria; hash de esta
   versión.
10. **Aceptación y STOP:** aceptar solo con cifras finitas justificadas,
    cobertura y corpus/hash revisables, cálculo concordante y decisión humana
    autenticada. STOP si hay máximo sin respaldo, consumidor no cubierto,
    discrepancia de fórmula/bytes, overflow, truncamiento, cambio de hash o
    solicitud de implementación/runtime sin gates y autorización propios.

`TECHNICALLY_PROPOSED`

`PENDING_HUMAN_APPROVAL`

No hay aprobación humana registrada en esta ficha. Ratificar NUM-C01 no
constituye por sí solo permiso G-IMP.

## H. Remaining Dependencies

- Decisión y acta NUM-C01 con autoridad y mandato verificables, valores
  ratificados, hash de esta ficha, alcance, reservas y fecha efectiva.
- Declaraciones de máximos de consumidores y corpus sintético versionado con
  procedencia, cobertura y hash, si se exige cerrar la brecha de evidencia de
  dominio.
- Cierre de las demás decisiones contractuales y de compatibilidad del freeze,
  incluida la autoridad aplicable, antes de levantar
  `S3-IMP-01 = BLOCKED_PENDING_AUTHORITY`.
- Autorización específica de implementación G-IMP posterior. No se concede por
  esta decisión ni se extiende a servicios, pruebas operacionales o fases
  posteriores.

## I. Git Integrity

Verificación de solo lectura al iniciar la tarea:

- Rama: `hardening/p0-p1-enterprise-readiness`.
- HEAD: `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`.
- La rama estaba adelantada dos commits respecto de `origin`.
- Ya existían cambios: `backend/config/settings.py` modificado; directorios/
  archivos sin seguimiento bajo `backend/apps/financial/`,
  `backend/scripts/` y `docs/financial/`.

Esta ficha es el único archivo creado por esta tarea dentro del directorio
`docs/financial/` que ya estaba sin seguimiento. No se modificaron archivos de
producto, pruebas, migraciones ni documentos históricos. No se ejecutaron
operaciones Git de escritura, commit, push, merge, reset ni checkout. El estado
anterior se preserva; la creación del archivo no cambia los estados de decisión
ni concede autorización.
