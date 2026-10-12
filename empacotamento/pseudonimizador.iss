; empacotamento/pseudonimizador.iss — Pseudonimizador-Setup.exe (spec §3). Compilado por construir.py
; com /DVersao e /DOrigem. Sem administrador; só x64; português do Brasil.
; SPDX-License-Identifier: AGPL-3.0-only
#ifndef Versao
  #error Passe /DVersao=x.y.z (construir.py faz isso)
#endif
#ifndef VersaoNum
  #define VersaoNum Versao
#endif
#ifndef Origem
  #define Origem "..\build\app"
#endif

[Setup]
AppId={{7D2B9C1E-5F3A-4B86-9E0C-2A6D4F8B1C57}
AppName=Pseudonimizador
AppVersion={#Versao}
AppVerName=Pseudonimizador {#Versao}
AppPublisher=Pseudonimizador — proteção de dados pessoais em documentos
VersionInfoVersion={#VersaoNum}.0
DefaultDirName={localappdata}\Programs\Pseudonimizador
DisableDirPage=yes
DefaultGroupName=Pseudonimizador
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
AppMutex=Pseudonimizador-Servidor
CloseApplications=yes
OutputDir=..\dist
OutputBaseFilename=Pseudonimizador-Setup
SetupIconFile=pseudonimizador.ico
UninstallDisplayIcon={app}\pseudonimizador.ico
UninstallDisplayName=Pseudonimizador
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Messages]
pt.WelcomeLabel2=O Pseudonimizador protege dados pessoais em documentos (DOCX e PDF) sem que nada saia do seu computador.%n%nEle será instalado só para você, sem precisar de administrador, e não baixa nada da internet.
pt.FinishedLabel=O Pseudonimizador está instalado. Abra-o pelo atalho e arraste um documento para a janela.

[Tasks]
Name: "atalho"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[InstallDelete]
; atualizar por cima não deixa arquivo velho (um módulo que sumiu, um .dist-info antigo). Só as pastas do
; programa; nunca {app} inteiro nem os dados em {localappdata}.
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\pseudonimizador"

[Files]
Source: "{#Origem}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Pseudonimizador"; Filename: "{app}\python\pythonw.exe"; Parameters: "-X utf8 -m pseudonimizador"; WorkingDir: "{app}"; IconFilename: "{app}\pseudonimizador.ico"; Comment: "Proteção de dados pessoais em documentos"
Name: "{group}\Desinstalar o Pseudonimizador"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Pseudonimizador"; Filename: "{app}\python\pythonw.exe"; Parameters: "-X utf8 -m pseudonimizador"; WorkingDir: "{app}"; IconFilename: "{app}\pseudonimizador.ico"; Tasks: atalho

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: "-X utf8 -m pseudonimizador"; WorkingDir: "{app}"; Description: "Abrir o Pseudonimizador agora"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; o que o programa criou em {app} depois da instalação (__pycache__). Os dados do usuário ({localappdata})
; só saem pela pergunta do Pascal; a pasta dos arquivos (Entrada, Saida, Mapas) NUNCA entra aqui.
Type: filesandordirs; Name: "{app}"

[Code]
var
  PaginaPasta: TInputDirWizardPage;
  ConfigFalhou, ApagarDadosResposta: Boolean;

function ConfigExiste: Boolean;
begin
  Result := FileExists(ExpandConstant('{localappdata}\Pseudonimizador\config.json'));
end;

procedure InitializeWizard;
begin
  PaginaPasta := CreateInputDirPage(wpWelcome, 'Pasta dos arquivos',
    'Onde ficam os documentos que você protege',
    'Nessa pasta o Pseudonimizador cria Entrada (documentos para processar em lote), Saida (os documentos protegidos) e Mapas (os mapas que permitem restaurar os nomes — guarde-os com cuidado). Dá para mudar depois, nas Configurações.',
    False, '');
  PaginaPasta.Add('');
  PaginaPasta.Values[0] := ExpandConstant('{userdocs}\Pseudonimizador');
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  // atualização por cima: a pasta já está no config.json e não é perguntada de novo
  Result := (PageID = PaginaPasta.ID) and ConfigExiste;
end;

function DentroDe(Pasta, Raiz: String): Boolean;
begin
  Pasta := Lowercase(AddBackslash(Trim(Pasta)));
  Raiz := Lowercase(AddBackslash(Raiz));
  Result := Copy(Pasta, 1, Length(Raiz)) = Raiz;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID <> PaginaPasta.ID then exit;
  if Trim(PaginaPasta.Values[0]) = '' then
  begin
    MsgBox('Informe a pasta dos arquivos.', mbInformation, MB_OK);
    Result := False;
  end
  else if DentroDe(PaginaPasta.Values[0], WizardDirValue) or
          DentroDe(PaginaPasta.Values[0], ExpandConstant('{localappdata}\Pseudonimizador')) then
  begin
    // WizardDirValue: a constante da pasta do programa ainda não existe nesta página. O desinstalador apaga essas duas pastas: os arquivos do usuário não podem ficar nelas
    MsgBox('A pasta dos arquivos não pode ficar dentro da pasta do programa nem da pasta de configurações do Pseudonimizador (a desinstalação poderia apagá-la). Escolha outra, como Documentos.', mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Codigo: Integer;
  Pasta: String;
begin
  if CurStep <> ssPostInstall then exit;
  if ConfigExiste then exit;
  // sem a barra final: "C:\x\" dentro de aspas viraria uma aspa escapada
  Pasta := RemoveBackslashUnlessRoot(Trim(PaginaPasta.Values[0]));
  if (not Exec(ExpandConstant('{app}\python\python.exe'),
      '-X utf8 -m pseudonimizador configurar --pasta-base "' + Pasta + '"',
      ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, Codigo)) or (Codigo <> 0) then
  begin
    ConfigFalhou := True;
    SuppressibleMsgBox('Não foi possível preparar a pasta dos arquivos (' + Pasta + '). ' +
      'O programa foi instalado; ao abrir, escolha a pasta em Configurações.', mbInformation, MB_OK, IDOK);
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  AlturaAntes: Integer;
begin
  if (CurPageID <> wpFinished) or (not ConfigFalhou) then exit;
  WizardForm.FinishedLabel.Caption := WizardForm.FinishedLabel.Caption + #13#10#13#10 +
    'A pasta dos arquivos não pôde ser preparada: escolha-a em Configurações ao abrir o programa.';
  // o texto mudou: reajusta a altura do rótulo e desloca a lista de "Executar" para não cortar nada
  AlturaAntes := WizardForm.FinishedLabel.Height;
  WizardForm.AdjustLabelHeight(WizardForm.FinishedLabel);
  WizardForm.RunList.Top := WizardForm.RunList.Top + (WizardForm.FinishedLabel.Height - AlturaAntes);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  // A pergunta vem depois do "Deseja remover completamente?" do próprio Inno. O padrão é NÃO
  // (MB_DEFBUTTON2) e a desinstalação silenciosa nunca apaga os dados (MsgBox comum não é suprimido
  // por /SUPPRESSMSGBOXES e o DelTree não passa pela Lixeira).
  if CurUninstallStep = usUninstall then
  begin
    if UninstallSilent then
      ApagarDadosResposta := False
    else
      ApagarDadosResposta := (MsgBox('Apagar também as configurações e os registros do Pseudonimizador neste computador (a pasta Pseudonimizador em AppData\Local)?' + #13#10#13#10 +
        'A pasta dos arquivos (Entrada, Saida e Mapas) nunca é apagada.', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES);
  end;
  if (CurUninstallStep = usPostUninstall) and ApagarDadosResposta then
    DelTree(ExpandConstant('{localappdata}\Pseudonimizador'), True, True, True);
end;
