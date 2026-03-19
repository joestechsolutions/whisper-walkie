; =============================================================================
; Whisper Walkie — NSIS Installer Script
; Uses NSIS Modern UI 2 (MUI2)
;
; Prerequisites:
;   - NSIS 3.x installed (https://nsis.sourceforge.io/)
;   - PyInstaller --onedir output at dist\WhisperWalkie\
;   - icon.ico in the same directory as this script
;   - LICENSE in the same directory as this script
;
; Build command (run from repo root):
;   makensis installer.nsi
;
; Output: dist\WhisperWalkie-Setup.exe
; =============================================================================

; ---------------------------------------------------------------------------
; MUI2 header — must be included before any Section or Function definitions
; ---------------------------------------------------------------------------
!include "MUI2.nsh"
!include "LogicLib.nsh"

; ---------------------------------------------------------------------------
; Installer metadata
; ---------------------------------------------------------------------------
!define APP_NAME        "Whisper Walkie"
!define APP_EXE         "WhisperWalkie.exe"
!define APP_DIR         "WhisperWalkie"
!define PUBLISHER       "Joe's Tech Solutions LLC"
!define WEBSITE         "https://www.joestechsolutions.com"
!define UNINST_KEY      "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR}"
!define INSTDIR_DEFAULT "$PROGRAMFILES64\${APP_DIR}"

; Version is injected by CI via /DAPP_VERSION=x.y.z, falls back to "1.0.0"
!ifndef APP_VERSION
  !define APP_VERSION "1.0.0"
!endif

; ---------------------------------------------------------------------------
; Compiler settings
; ---------------------------------------------------------------------------
Name              "${APP_NAME} ${APP_VERSION}"
OutFile           "dist\WhisperWalkie-Setup.exe"
InstallDir        "${INSTDIR_DEFAULT}"
InstallDirRegKey  HKLM "${UNINST_KEY}" "InstallLocation"

; Request elevation — writing to Program Files requires admin privileges.
RequestExecutionLevel admin

; Show install/uninstall details by default so the user can see progress
ShowInstDetails   show
ShowUninstDetails show

; Enable CRC checking of the installer itself
CRCCheck on

; Use solid LZMA compression — best ratio for a large PyInstaller bundle
SetCompressor /SOLID lzma

; ---------------------------------------------------------------------------
; Version info embedded into the installer .exe
; ---------------------------------------------------------------------------
VIProductVersion  "${APP_VERSION}.0"
VIAddVersionKey   "ProductName"      "${APP_NAME}"
VIAddVersionKey   "ProductVersion"   "${APP_VERSION}"
VIAddVersionKey   "CompanyName"      "${PUBLISHER}"
VIAddVersionKey   "LegalCopyright"   "Copyright (c) ${PUBLISHER}"
VIAddVersionKey   "FileDescription"  "${APP_NAME} Installer"
VIAddVersionKey   "FileVersion"      "${APP_VERSION}"

; ---------------------------------------------------------------------------
; MUI2 settings
; ---------------------------------------------------------------------------
!define MUI_ICON   "icon.ico"
!define MUI_UNICON "icon.ico"

; Finish page: offer to launch the app after install
!define MUI_FINISHPAGE_RUN         "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT    "Launch ${APP_NAME}"
!define MUI_FINISHPAGE_LINK        "Visit ${WEBSITE}"
!define MUI_FINISHPAGE_LINK_LOCATION "${WEBSITE}"

; Abort confirmation on cancel during install
!define MUI_ABORTWARNING

; ---------------------------------------------------------------------------
; Installer pages
; ---------------------------------------------------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE   "LICENSE"       ; Shows MIT license text
!insertmacro MUI_PAGE_DIRECTORY                 ; Let user choose install dir
!insertmacro MUI_PAGE_COMPONENTS                ; Desktop shortcut checkbox
!insertmacro MUI_PAGE_INSTFILES                 ; Progress bar
!insertmacro MUI_PAGE_FINISH

; ---------------------------------------------------------------------------
; Uninstaller pages
; ---------------------------------------------------------------------------
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ---------------------------------------------------------------------------
; Language (must come after page macros)
; ---------------------------------------------------------------------------
!insertmacro MUI_LANGUAGE "English"

; ---------------------------------------------------------------------------
; Install sections
; ---------------------------------------------------------------------------

; Core application files — always installed, not toggleable
Section "${APP_NAME}" SecCore
  ; Mark as required so the user cannot deselect it
  SectionIn RO

  SetOutPath "$INSTDIR"

  ; Copy entire PyInstaller --onedir output tree.
  ; The trailing \*.* ensures subdirectories are included recursively.
  File /r "dist\${APP_DIR}\*.*"

  ; --- Start Menu shortcut ---
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut  "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
                  "$INSTDIR\${APP_EXE}" \
                  "" \
                  "$INSTDIR\${APP_EXE}" 0 \
                  SW_SHOWNORMAL \
                  "" \
                  "Push-to-talk speech-to-text"

  CreateShortcut  "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk" \
                  "$INSTDIR\uninstall.exe"

  ; --- Uninstaller ---
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; --- Add/Remove Programs registry entry ---
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayName"          "${APP_NAME}"
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayVersion"        "${APP_VERSION}"
  WriteRegStr   HKLM "${UNINST_KEY}" "Publisher"             "${PUBLISHER}"
  WriteRegStr   HKLM "${UNINST_KEY}" "URLInfoAbout"          "${WEBSITE}"
  WriteRegStr   HKLM "${UNINST_KEY}" "InstallLocation"       "$INSTDIR"
  WriteRegStr   HKLM "${UNINST_KEY}" "UninstallString"       '"$INSTDIR\uninstall.exe"'
  WriteRegStr   HKLM "${UNINST_KEY}" "QuietUninstallString"  '"$INSTDIR\uninstall.exe" /S'
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayIcon"           "$INSTDIR\${APP_EXE}"
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify"              1
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair"              1

  ; Estimated install size in KB — helps Add/Remove Programs display a size.
  ; PyInstaller bundles with Whisper model are typically 500–800 MB.
  ; This is a conservative estimate; NSIS can calculate it automatically via
  ; the EstimatedSize plugin, but a static value avoids the extra dependency.
  WriteRegDWORD HKLM "${UNINST_KEY}" "EstimatedSize"         700000

SectionEnd

; Optional desktop shortcut — shown as a checkbox on the Components page
Section /o "Desktop Shortcut" SecDesktop
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" \
                 "$INSTDIR\${APP_EXE}" \
                 "" \
                 "$INSTDIR\${APP_EXE}" 0 \
                 SW_SHOWNORMAL \
                 "" \
                 "Push-to-talk speech-to-text"
SectionEnd

; ---------------------------------------------------------------------------
; MUI2 section descriptions (shown in the Components page tooltip)
; ---------------------------------------------------------------------------
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCore}    \
    "Installs ${APP_NAME} and Start Menu shortcuts. Required."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} \
    "Adds a shortcut to your Desktop for quick access."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ---------------------------------------------------------------------------
; Uninstaller section
; ---------------------------------------------------------------------------
Section "Uninstall"

  ; Remove all installed files.
  ; RMDir /r removes the whole directory — safe because we own $INSTDIR.
  RMDir /r "$INSTDIR"

  ; Remove Start Menu folder
  RMDir /r "$SMPROGRAMS\${APP_NAME}"

  ; Remove Desktop shortcut if it exists
  Delete "$DESKTOP\${APP_NAME}.lnk"

  ; Remove Add/Remove Programs registry entry
  DeleteRegKey HKLM "${UNINST_KEY}"

SectionEnd
