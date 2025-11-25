import typer
import asyncio
from sqlalchemy import select
from models.entity import User
from postgres import create_database, get_session

app = typer.Typer()


@app.command()
def create_superuser(
    login: str = typer.Argument(..., help="Логин пользователя"),
    password: str = typer.Argument(..., help="Пароль"),
    email: str = typer.Argument(..., help="Email пользователя"),
):
    asyncio.run(async_create_superuser(login, password, email))


async def async_create_superuser(login: str, password: str, email: str):

    await create_database()

    session_gen = get_session()
    session = await session_gen.__anext__()

    try:
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            typer.echo(f"Пользователь '{email}' уже существует!")
            return

        user = User(login=login, password=password, email=email)
        user.is_superuser = True

        session.add(user)
        await session.commit()

        typer.echo(f"Суперпользователь '{email}' создан!")

    except Exception as e:
        await session.rollback()
        typer.echo(f"Ошибка: {e}")

    finally:
        try:
            await session_gen.aclose()
        except Exception:
            pass


if __name__ == "__main__":
    app()
# Вызвать в ручную
# docker-compose exec КОНТЕЙНЕР python /app/db/pg_superuser_cli.py admin 123 admin@gmail.com
