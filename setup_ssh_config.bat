@echo off
if not exist "%USERPROFILE%\.ssh" mkdir "%USERPROFILE%\.ssh"
echo Host gamenews> "%USERPROFILE%\.ssh\config"
echo     HostName 8.134.13.73>> "%USERPROFILE%\.ssh\config"
echo     User root>> "%USERPROFILE%\.ssh\config"
echo     IdentityFile %USERPROFILE%\.ssh\id_rsa>> "%USERPROFILE%\.ssh\config"
echo SSH config has been set up. You can now use 'ssh gamenews' to connect to the server.
