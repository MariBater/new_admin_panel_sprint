import typer
import asyncio
from sqlalchemy import select
from auth_service.src.models.entity import Role, User
from auth_service.src.db.postgres import create_database, get_session

app = typer.Typer()


@app.command()
def create_superuser(
    login: str = typer.Argument(..., help="Логин пользователя"),
    password: str = typer.Argument(..., help="Пароль"),
    email: str = typer.Argument(..., help="Email пользователя"),
):
    asyncio.run(async_create_superuser(login, password, email))


async def _get_or_create_role(session, role_name: str) -> Role:

    result = await session.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()

    if not role:
        role = Role(name=role_name)
        session.add(role)
        await session.flush()

    return role


async def async_create_superuser(login: str, password: str, email: str):

    await create_database()

    async for session in get_session():
        try:
            result = await session.execute(select(User).where(User.email == email))
            if result.scalar_one_or_none():
                typer.echo(f"Пользователь '{email}' уже существует")
                return

            admin_role = await _get_or_create_role(session, "admin")
            await _get_or_create_role(session, "user")
            await _get_or_create_role(session, "premium_user")

            user = User(
                login=login,
                email=email,
                password=password,
            )
            user.is_superuser = True

            user.roles.append(admin_role)

            session.add(user)
            await session.commit()

            typer.echo(f"Суперпользователь '{email}' успешно создан")

        except Exception as e:
            await session.rollback()
            typer.echo(f"Ошибка: {e}")
            raise


if __name__ == "__main__":
    app()
# Вызвать в ручную
# docker-compose exec auth-service python /app/src/db/pg_superuser_cli.py admin 123 admin@gmail.com
