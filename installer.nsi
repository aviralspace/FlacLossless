; FlacLossless Installer (NSIS)
; Run with: makensis installer.nsi

!include "MUI2.nsh"
!include "x64.nsh"

; Installer settings
Name "FlacLossless"
OutFile "FlacLossless-Setup.exe"
InstallDir "$PROGRAMFILES\FlacLossless"
RequestExecutionLevel admin

; UI settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

; Sections
Section "Install FlacLossless"
  SetOutPath "$INSTDIR"
  
  ; Copy all files from FlacLossless-main to installation dir
  File /r "FlacLossless-main\*.*"
  File /r ".venv" ; Include pre-built venv if exists
  
  ; Create Python venv if not present
  ${If} ${FileExists} "$INSTDIR\.venv"
    DetailPrint "Virtual environment already exists"
  ${Else}
    DetailPrint "Creating Python virtual environment..."
    nsExec::ExecToLog 'py -m venv "$INSTDIR\.venv"'
  ${EndIf}
  
  ; Install Python dependencies
  DetailPrint "Installing Python dependencies..."
  nsExec::ExecToLog '"$INSTDIR\.venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel'
  nsExec::ExecToLog '"$INSTDIR\.venv\Scripts\python.exe" -m pip install -r "$INSTDIR\backend\requirements.txt"'
  
  ; Install Node dependencies
  ${If} ${FileExists} "$INSTDIR\node_modules"
    DetailPrint "Node modules already exist"
  ${Else}
    DetailPrint "Installing Node dependencies..."
    nsExec::ExecToLog 'npm install --silent'
  ${EndIf}
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\FlacLossless"
  CreateShortCut "$SMPROGRAMS\FlacLossless\FlacLossless.lnk" "$INSTDIR\run_windows.bat" "" "$INSTDIR\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\FlacLossless\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  
  ; Create desktop shortcut
  CreateShortCut "$DESKTOP\FlacLossless.lnk" "$INSTDIR\run_windows.bat" "" "$INSTDIR\icon.ico" 0
  
  ; Write uninstall info
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FlacLossless" "DisplayName" "FlacLossless"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FlacLossless" "UninstallString" "$INSTDIR\uninstall.exe"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  DetailPrint "Installation complete!"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\FlacLossless"
  Delete "$DESKTOP\FlacLossless.lnk"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FlacLossless"
SectionEnd
