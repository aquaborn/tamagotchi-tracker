@echo off
REM Файл для локального запуска TMA Tamagotchi
REM Перед запуском убедитесь, что установлены: Docker, docker-compose

echo Запуск TMA Tamagotchi...
echo.

cd /d %~dp0

echo Убедитесь, что Docker Desktop запущен...
echo.

echo Останавливаем существующие контейнеры...
docker-compose -f compose.yaml down

echo Запускаем контейнеры...
docker-compose -f compose.yaml up -d

echo.
echo Проверяем статус контейнеров...
docker-compose -f compose.yaml ps

echo.
echo Проект запущен!
echo API доступно на http://localhost:8000
echo База данных доступна на http://localhost:5432
echo.
echo Для остановки используйте: docker-compose -f compose.yaml down
echo.

pause