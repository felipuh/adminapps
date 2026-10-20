"""Prepared only; PostgreSQL authority writes cannot resurrect human JWTs."""
from django.db import migrations, models

FORWARD = r"""
CREATE FUNCTION adminapps_human_authority() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.password IS DISTINCT FROM NEW.password
     OR OLD.is_active IS DISTINCT FROM NEW.is_active THEN
    NEW.human_auth_version := OLD.human_auth_version + 1;
    UPDATE user_sessions SET is_active=false, revoked_at=clock_timestamp(),
           generation=generation+1,
           revocation_reason=CASE WHEN OLD.password IS DISTINCT FROM NEW.password
                                  THEN 'password_change' ELSE 'user_activity_change' END
    WHERE user_id=OLD.id AND contract_version=1 AND is_active AND revoked_at IS NULL;
  ELSE
    -- Stale ORM instances and raw updates cannot roll authority backwards.
    NEW.human_auth_version := OLD.human_auth_version;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER adminapps_human_authority BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION adminapps_human_authority();
CREATE FUNCTION adminapps_human_session_monotonic() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.contract_version <> 1 THEN RETURN NEW; END IF;
  IF ROW(NEW.id,NEW.user_id,NEW.contract_version,NEW.token_family,NEW.family_id,
         NEW.authority_version,NEW.created_at,NEW.expires_at)
     IS DISTINCT FROM
     ROW(OLD.id,OLD.user_id,OLD.contract_version,OLD.token_family,OLD.family_id,
         OLD.authority_version,OLD.created_at,OLD.expires_at)
     OR NEW.generation < OLD.generation
     OR (NOT OLD.is_active AND NEW.is_active)
     OR (OLD.revoked_at IS NOT NULL AND
         ROW(NEW.revoked_at,NEW.revocation_reason,NEW.token_jti,NEW.generation,NEW.is_active)
         IS DISTINCT FROM ROW(OLD.revoked_at,OLD.revocation_reason,OLD.token_jti,OLD.generation,OLD.is_active))
     OR (ROW(NEW.token_jti,NEW.is_active,NEW.revoked_at)
         IS DISTINCT FROM ROW(OLD.token_jti,OLD.is_active,OLD.revoked_at)
         AND NEW.generation <= OLD.generation)
     OR (NEW.is_active AND NEW.revoked_at IS NOT NULL)
  THEN RAISE EXCEPTION 'Invalid human session transition'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER adminapps_human_session_monotonic BEFORE UPDATE ON user_sessions
FOR EACH ROW EXECUTE FUNCTION adminapps_human_session_monotonic();
"""
REVERSE = """
DROP TRIGGER adminapps_human_session_monotonic ON user_sessions;
DROP FUNCTION adminapps_human_session_monotonic();
DROP TRIGGER adminapps_human_authority ON users;
DROP FUNCTION adminapps_human_authority();
"""


def install(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        raise RuntimeError('Human JWT authority requires PostgreSQL')
    schema_editor.execute(FORWARD)


def uninstall(apps, schema_editor):
    schema_editor.execute(REVERSE)


class Migration(migrations.Migration):
    dependencies = [('users', '0004_transactional_2fa')]
    operations = [
        migrations.AddField('user', 'human_auth_version', models.PositiveBigIntegerField(default=1, editable=False)),
        migrations.AddField('usersession', 'contract_version', models.PositiveSmallIntegerField(default=0, editable=False)),
        migrations.AddField('usersession', 'token_family', models.CharField(max_length=40, default='', editable=False)),
        migrations.AddField('usersession', 'family_id', models.UUIDField(null=True, unique=True, editable=False)),
        migrations.AddField('usersession', 'generation', models.PositiveBigIntegerField(default=1, editable=False)),
        migrations.AddField('usersession', 'authority_version', models.PositiveBigIntegerField(default=0, editable=False)),
        migrations.AddField('usersession', 'revoked_at', models.DateTimeField(null=True, blank=True, editable=False)),
        migrations.AddField('usersession', 'revocation_reason', models.CharField(max_length=80, blank=True, editable=False)),
        migrations.RunPython(install, uninstall),
    ]
