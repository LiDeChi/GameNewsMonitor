@echo off
echo Setting up SSH key...
echo First, we'll copy your public key content:
type %USERPROFILE%\.ssh\id_ed25519.pub
echo.
echo Please copy the above key content.
echo.
echo Now connecting to the server to set up the key...
echo When connected, please run these commands:
echo mkdir -p ~/.ssh
echo nano ~/.ssh/authorized_keys
echo Paste the key content, then press Ctrl+X, Y, and Enter to save
echo chmod 600 ~/.ssh/authorized_keys
echo chmod 700 ~/.ssh
echo.
ssh root@8.134.13.73
