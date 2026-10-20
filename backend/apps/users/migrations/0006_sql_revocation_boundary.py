"""Retain authority history; pair with the separately provisioned runtime ACL.

Irreversible by design: recovery must preserve committed revocations. This does
not defend against an owner/administrator who can disable or replace triggers.
"""
from django.db import migrations


FORWARD = """
CREATE FUNCTION public.adminapps_retain_authority() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER
SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
  RAISE EXCEPTION 'Authority history cannot be deleted or truncated'
    USING ERRCODE = '23514';
END $$;
REVOKE ALL ON FUNCTION public.adminapps_retain_authority() FROM PUBLIC;
"""

for table in (
    "user_sessions", "sso_sessions", "sso_security_fence",
    "sso_revocation_outbox",
):
    FORWARD += f"""
CREATE TRIGGER adminapps_retain_authority_delete
BEFORE DELETE ON public.{table}
FOR EACH ROW EXECUTE FUNCTION public.adminapps_retain_authority();
CREATE TRIGGER adminapps_retain_authority_truncate
BEFORE TRUNCATE ON public.{table}
FOR EACH STATEMENT EXECUTE FUNCTION public.adminapps_retain_authority();
"""

# Existing invoker functions must resolve authority tables in the trusted schema.
for function in (
    "adminapps_human_authority", "adminapps_human_session_monotonic",
    "sso_revoke_authority", "sso_session_monotonic", "sso_fence_monotonic",
    "sso_activation_reset",
):
    FORWARD += (
        f"ALTER FUNCTION public.{function}() "
        "SET search_path = pg_catalog, public, pg_temp;\n"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0005_human_jwt_sessions"),
        ("integration", "0010_sso_authority_fence"),
    ]
    operations = [migrations.RunSQL(FORWARD)]
