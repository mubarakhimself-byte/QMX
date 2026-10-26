<!--
source_url: https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid
fetched_from: https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid?accept=text/markdown
title: KNOWNFOLDERID (Win32 Shell)
fetched: 2026-10-26
fetched_by: research agent for study 62b (raw text as served)
-->

---
layout: Conceptual
title: KNOWNFOLDERID (Knownfolders.h) - Win32 apps | Microsoft Learn
canonicalUrl: https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid
breadcrumb_path: /windows/desktop/breadcrumb/toc.json
uhfHeaderId: MSDocsHeader-WinDevCenter
recommendations: true
adobe-target: true
ms.service: windows-api-desktop-tech
ms.subservice: desktop-environment
ms.author: jken
author: GrantMeStrength
feedback_system: Standard
feedback_product_url: https://www.microsoft.com/en-us/windowsinsider/feedbackhub/fb
feedback_help_link_url: https://learn.microsoft.com/answers/tags/224/windows-api-win32/
feedback_help_link_type: get-help-at-qna
description: The KNOWNFOLDERID constants represent GUIDs that identify standard folders registered with the system as Known Folders.
ms.assetid: f2c08ade-3083-44e4-82b0-dde45f0e3094
ms.topic: reference
ms.custom: snippet-project
ms.date: 2020-07-27T00:00:00.0000000Z
locale: en-us
document_id: 57c30ded-50d7-1768-4fb9-6ba57dbac75d
document_version_independent_id: 074b8b82-8b22-7e96-e28c-56c0c98d2955
updated_at: 2023-08-30T21:45:00.0000000Z
original_content_git_url: https://github.com/MicrosoftDocs/win32-pr/blob/live/desktop-src/shell/knownfolderid.md
gitcommit: https://github.com/MicrosoftDocs/win32-pr/blob/efcbb0ee79ea508ffa68105c61d096606aee1b4f/desktop-src/shell/knownfolderid.md
git_commit_id: efcbb0ee79ea508ffa68105c61d096606aee1b4f
site_name: Docs
depot_name: MSDN.win32
page_type: conceptual
toc_rel: toc.json
pdf_url_template: https://learn.microsoft.com/pdfstore/en-us/MSDN.win32/{branchName}{pdfName}
word_count: 4458
asset_id: shell/knownfolderid
moniker_range_name: 
monikers: []
item_type: Content
source_path: desktop-src/shell/knownfolderid.md
cmProducts:
- https://authoring-docs-microsoft.poolparty.biz/devrel/bcbcbad5-4208-4783-8035-8481272c98b8
spProducts:
- https://authoring-docs-microsoft.poolparty.biz/devrel/43b2e5aa-8a6d-4de2-a252-692232e5edc8
platformId: 748fc166-f6d3-19b0-6d93-aa0a7918105b
---

# KNOWNFOLDERID (Knownfolders.h) - Win32 apps | Microsoft Learn

The **KNOWNFOLDERID** constants represent GUIDs that identify standard folders registered with the system as [Known Folders](known-folders). These folders are installed with Windows Vista and later operating systems, and a computer will have only folders appropriate to it installed. For descriptions of these folders, see [**CSIDL**](csidl).

## Example

```c
HRESULT CExplorerBrowserHostDialog::_FillViewWithKnownFolders(IResultsFolder *prf)
{
    IKnownFolderManager *pManager;
    HRESULT hr = CoCreateInstance(CLSID_KnownFolderManager, NULL, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&pManager));
    if (SUCCEEDED(hr))
    {
        UINT cCount;
        KNOWNFOLDERID *pkfid;

        hr = pManager->GetFolderIds(&pkfid, &cCount);
        if (SUCCEEDED(hr))
        {
            for (UINT i = 0; i < cCount; i++)
            {
                IKnownFolder *pKnownFolder;
                hr = pManager->GetFolder(pkfid[i], &pKnownFolder);
                if (SUCCEEDED(hr))
                {
                    IShellItem *psi;
                    hr = pKnownFolder->GetShellItem(0, IID_PPV_ARGS(&psi));
                    if (SUCCEEDED(hr))
                    {
                        hr = prf->AddItem(psi);
                        psi->Release();
                    }
                    pKnownFolder->Release();
                }
            }
            CoTaskMemFree(pkfid);
        }
        pManager->Release();
    }
    return hr;
}

```

Example from [Windows classic samples](https://github.com/microsoft/Windows-classic-samples/blob/1d363ff4bd17d8e20415b92e2ee989d615cc0d91/Samples/Win7Samples/winui/shell/appplatform/ExplorerBrowserCustomContents/ExplorerBrowserCustomContents.cpp) on GitHub.

## Constants

| Constant | Description |
| --- | --- |
| - **FOLDERID\_AccountPictures** | | GUID | {008ca0b1-55b4-4c56-b8a8-4de4b299d3be} |<br>| --- | --- |<br>| Display Name | Account Pictures |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\AccountPictures |<br>| CSIDL Equivalent | None, value introduced in Windows 8 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_AddNewPrograms** | | GUID | {de61d971-5ebc-4f02-a3a9-6c82895e5c04} |<br>| --- | --- |<br>| Display Name | Get Programs |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Add New Programs (found in the **Add or Remove Programs** item in the Control Panel) |<br>| Legacy Default Path | Not applicable—virtual folder | |
| - **FOLDERID\_AdminTools** | | GUID | {724EF170-A42D-4FEF-9F26-B60E846FBA4F} |<br>| --- | --- |<br>| Display Name | Administrative Tools |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Start Menu\Programs\Administrative Tools |<br>| CSIDL Equivalent | CSIDL\_ADMINTOOLS |<br>| Legacy Display Name | Administrative Tools |<br>| Legacy Default Path | %USERPROFILE%\Start Menu\Programs\Administrative Tools | |
| - **FOLDERID\_AppDataDesktop** | | GUID | {B2C5E279-7ADD-439F-B28C-C41FE1BBF672} |<br>| --- | --- |<br>| Display Name | AppDataDesktop |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Desktop |<br>| CSIDL Equivalent | None, value introduced in Windows 10, version 1709 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable |<br><br><br>This FOLDERID is used internally by .NET applications to enable cross-platform app functionality. It is not intended to be used directly from an application. |
| - **FOLDERID\_AppDataDocuments** | | GUID | {7BE16610-1F7F-44AC-BFF0-83E15F2FFCA1} |<br>| --- | --- |<br>| Display Name | AppDataDocuments |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Documents |<br>| CSIDL Equivalent | None, value introduced in Windows 10, version 1709 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable |<br><br><br>This FOLDERID is used internally by .NET applications to enable cross-platform app functionality. It is not intended to be used directly from an application. |
| - **FOLDERID\_AppDataFavorites** | | GUID | {7CFBEFBC-DE1F-45AA-B843-A542AC536CC9} |<br>| --- | --- |<br>| Display Name | AppDataFavorites |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Favorites |<br>| CSIDL Equivalent | None, value introduced in Windows 10, version 1709 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable |<br><br><br>This FOLDERID is used internally by .NET applications to enable cross-platform app functionality. It is not intended to be used directly from an application. |
| - **FOLDERID\_AppDataProgramData** | | GUID | {559D40A3-A036-40FA-AF61-84CB430A4D34} |<br>| --- | --- |<br>| Display Name | AppDataProgramData |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\ProgramData |<br>| CSIDL Equivalent | None, value introduced in Windows 10, version 1709 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable |<br><br><br>This FOLDERID is used internally by .NET applications to enable cross-platform app functionality. It is not intended to be used directly from an application. |
| - **FOLDERID\_ApplicationShortcuts** | | GUID | {A3918781-E5F2-4890-B3D9-A7E54332328C} |<br>| --- | --- |<br>| Display Name | Application Shortcuts |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\Application Shortcuts |<br>| CSIDL Equivalent | None, value introduced in Windows 8 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_AppsFolder** | | GUID | {1e87508d-89c2-42f0-8a7e-645a0f50ca58} |<br>| --- | --- |<br>| Display Name | Applications |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None, value introduced in Windows 8 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_AppUpdates** | | GUID | {a305ce99-f527-492b-8b1a-7e76fa98d6e4} |<br>| --- | --- |<br>| Display Name | Installed Updates |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | None, value introduced in Windows Vista. In earlier versions of Windows, the information on this page was included in **Add or Remove Programs** if the **Show updates** box was checked. |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_CameraRoll** | | GUID | {AB5FB87B-7CE2-4F83-915D-550846C9537B} |<br>| --- | --- |<br>| Display Name | Camera Roll |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Pictures\Camera Roll |<br>| CSIDL Equivalent | None, value introduced in Windows 8.1 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_CDBurning** | | GUID | {9E52AB10-F80D-49DF-ACB8-4330F5687855} |<br>| --- | --- |<br>| Display Name | Temporary Burn Folder |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\Burn\Burn |<br>| CSIDL Equivalent | CSIDL\_CDBURN\_AREA |<br>| Legacy Display Name | CD Burning |<br>| Legacy Default Path | %USERPROFILE%\Local Settings\Application Data\Microsoft\CD Burning | |
| - **FOLDERID\_ChangeRemovePrograms** | | GUID | {df7266ac-9274-4867-8d55-3bd661de872d} |<br>| --- | --- |<br>| Display Name | Programs and Features |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Add or Remove Programs |<br>| Legacy Default Path | Not applicable—virtual folder | |
| - **FOLDERID\_CommonAdminTools** | | GUID | {D0384E7D-BAC3-4797-8F14-CBA229B392B5} |<br>| --- | --- |<br>| Display Name | Administrative Tools |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\Microsoft\Windows\Start Menu\Programs\Administrative Tools |<br>| CSIDL Equivalent | CSIDL\_COMMON\_ADMINTOOLS |<br>| Legacy Display Name | Administrative Tools |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Start Menu\Programs\Administrative Tools | |
| - **FOLDERID\_CommonOEMLinks** | | GUID | {C1BAE2D0-10DF-4334-BEDD-7AA20B227A9D} |<br>| --- | --- |<br>| Display Name | OEM Links |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\OEM Links |<br>| CSIDL Equivalent | CSIDL\_COMMON\_OEM\_LINKS |<br>| Legacy Display Name | OEM Links |<br>| Legacy Default Path | %ALLUSERSPROFILE%\OEM Links | |
| - **FOLDERID\_CommonPrograms** | | GUID | {0139D44E-6AFE-49F2-8690-3DAFCAE6FFB8} |<br>| --- | --- |<br>| Display Name | Programs |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\Microsoft\Windows\Start Menu\Programs |<br>| CSIDL Equivalent | CSIDL\_COMMON\_PROGRAMS |<br>| Legacy Display Name | Programs |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Start Menu\Programs | |
| - **FOLDERID\_CommonStartMenu** | | GUID | {A4115719-D62E-491D-AA7C-E74B8BE3B067} |<br>| --- | --- |<br>| Display Name | Start Menu |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\Microsoft\Windows\Start Menu |<br>| CSIDL Equivalent | CSIDL\_COMMON\_STARTMENU |<br>| Legacy Display Name | Start Menu |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Start Menu | |
| - **FOLDERID\_CommonStartup** | | GUID | {82A5EA35-D9CD-47C5-9629-E15D2F714E6E} |<br>| --- | --- |<br>| Display Name | Startup |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\Microsoft\Windows\Start Menu\Programs\StartUp |<br>| CSIDL Equivalent | CSIDL\_COMMON\_STARTUP, CSIDL\_COMMON\_ALTSTARTUP |<br>| Legacy Display Name | Startup |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Start Menu\Programs\StartUp | |
| - **FOLDERID\_CommonTemplates** | | GUID | {B94237E7-57AC-4347-9151-B08C6C32D1F7} |<br>| --- | --- |<br>| Display Name | Templates |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\Microsoft\Windows\Templates |<br>| CSIDL Equivalent | CSIDL\_COMMON\_TEMPLATES |<br>| Legacy Display Name | Templates |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Templates | |
| - **FOLDERID\_ComputerFolder** | | GUID | {0AC0837C-BBF8-452A-850D-79D08E667CA7} |<br>| --- | --- |<br>| Display Name | Computer |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | CSIDL\_DRIVES |<br>| Legacy Display Name | My Computer |<br>| Legacy Default Path | Not applicable—virtual folder | |
| - **FOLDERID\_ConflictFolder** | | GUID | {4bfefb45-347d-4006-a5be-ac0cb0567192} |<br>| --- | --- |<br>| Display Name | Conflicts |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable. This **KNOWNFOLDERID** refers to the Windows Vista Synchronization Manager. It is not the folder referenced by the older [**ISyncMgrConflictFolder**](/en-us/windows/desktop/api/Syncmgr/nn-syncmgr-isyncmgrconflictfolder). |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_ConnectionsFolder** | | GUID | {6F0CD92B-2E97-45D1-88FF-B0D186B8DEDD} |<br>| --- | --- |<br>| Display Name | Network Connections |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | CSIDL\_CONNECTIONS |<br>| Legacy Display Name | Network Connections |<br>| Legacy Default Path | Not applicable—virtual folder | |
| - **FOLDERID\_Contacts** | | GUID | {56784854-C6CB-462b-8169-88E350ACB882} |<br>| --- | --- |<br>| Display Name | Contacts |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Contacts |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_ControlPanelFolder** | | GUID | {82A74AEB-AEB4-465C-A014-D097EE346D63} |<br>| --- | --- |<br>| Display Name | Control Panel |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | CSIDL\_CONTROLS |<br>| Legacy Display Name | Control Panel |<br>| Legacy Default Path | Not applicable—virtual folder | |
| - **FOLDERID\_Cookies** | | GUID | {2B0F765D-C0E9-4171-908E-08A611B84FF6} |<br>| --- | --- |<br>| Display Name | Cookies |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Cookies |<br>| CSIDL Equivalent | CSIDL\_COOKIES |<br>| Legacy Display Name | Cookies |<br>| Legacy Default Path | %USERPROFILE%\Cookies | |
| - **FOLDERID\_Desktop** | | GUID | {B4BFCC3A-DB2C-424C-B029-7FE99A87C641} |<br>| --- | --- |<br>| Display Name | Desktop |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Desktop |<br>| CSIDL Equivalent | CSIDL\_DESKTOP, CSIDL\_DESKTOPDIRECTORY |<br>| Legacy Display Name | Desktop |<br>| Legacy Default Path | %USERPROFILE%\Desktop | |
| - **FOLDERID\_DeviceMetadataStore** | | GUID | {5CE4A5E9-E4EB-479D-B89F-130C02886155} |<br>| --- | --- |<br>| Display Name | DeviceMetadataStore |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\Microsoft\Windows\DeviceMetadataStore |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_Documents** | | GUID | {FDD39AD0-238F-46AF-ADB4-6C85480369C7} |<br>| --- | --- |<br>| Display Name | Documents |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Documents |<br>| CSIDL Equivalents | CSIDL\_MYDOCUMENTS, CSIDL\_PERSONAL |<br>| Legacy Display Name | My Documents |<br>| Legacy Default Path | %USERPROFILE%\My Documents | |
| - **FOLDERID\_DocumentsLibrary** | | GUID | {7B0DB17D-9CD2-4A93-9733-46CC89022E7C} |<br>| --- | --- |<br>| Display Name | Documents |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Libraries\Documents.library-ms |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_Downloads** | | GUID | {374DE290-123F-4565-9164-39C4925E467B} |<br>| --- | --- |<br>| Display Name | Downloads |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Downloads |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_Favorites** | | GUID | {1777F761-68AD-4D8A-87BD-30B759FA33DD} |<br>| --- | --- |<br>| Display Name | Favorites |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Favorites |<br>| CSIDL Equivalent | CSIDL\_FAVORITES, CSIDL\_COMMON\_FAVORITES |<br>| Legacy Display Name | Favorites |<br>| Legacy Default Path | %USERPROFILE%\Favorites | |
| - **FOLDERID\_Fonts** | | GUID | {FD228CB7-AE11-4AE3-864C-16F3910AB8FE} |<br>| --- | --- |<br>| Display Name | Fonts |<br>| Folder Type | FIXED |<br>| Default Path | %windir%\Fonts |<br>| CSIDL Equivalent | CSIDL\_FONTS |<br>| Legacy Display Name | Fonts |<br>| Legacy Default Path | %windir%\Fonts | |
| - **FOLDERID\_Games** | **Note:** This FOLDERID is deprecated in Windows 10, version 1803 and later versions. In these versions, it returns **0x80070057 - E\_INVALIDARG**<br><br><br>| GUID | {CAC52C1A-B53D-4edc-92D7-6B2E8AC19434} |<br>| --- | --- |<br>| Display Name | Games |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_GameTasks** | | GUID | {054FAE61-4DD8-4787-80B6-090220C4B700} |<br>| --- | --- |<br>| Display Name | GameExplorer |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\GameExplorer |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_History** | | GUID | {D9DC8A3B-B784-432E-A781-5A1130A75963} |<br>| --- | --- |<br>| Display Name | History |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\History |<br>| CSIDL Equivalent | CSIDL\_HISTORY |<br>| Legacy Display Name | History |<br>| Legacy Default Path | %USERPROFILE%\Local Settings\History | |
| - **FOLDERID\_HomeGroup** | | GUID | {52528A6B-B9E3-4ADD-B60D-588C2DBA842D} |<br>| --- | --- |<br>| Display Name | Homegroup |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_HomeGroupCurrentUser** | | GUID | {9B74B6A3-0DFD-4f11-9E78-5F7800F2E772} |<br>| --- | --- |<br>| Display Name | The user's username (%USERNAME%) |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None, value introduced in Windows 8 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_ImplicitAppShortcuts** | | GUID | {BCB5256F-79F6-4CEE-B725-DC34E402FD46} |<br>| --- | --- |<br>| Display Name | ImplicitAppShortcuts |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Internet Explorer\Quick Launch\User Pinned\ImplicitAppShortcuts |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_InternetCache** | | GUID | {352481E8-33BE-4251-BA85-6007CAEDCF9D} |<br>| --- | --- |<br>| Display Name | Temporary Internet Files |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\Temporary Internet Files |<br>| CSIDL Equivalent | CSIDL\_INTERNET\_CACHE |<br>| Legacy Display Name | Temporary Internet Files |<br>| Legacy Default Path | %USERPROFILE%\Local Settings\Temporary Internet Files | |
| - **FOLDERID\_InternetFolder** | | GUID | {4D9F7874-4E0C-4904-967B-40B0D20C3E4B} |<br>| --- | --- |<br>| Display Name | The Internet |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | CSIDL\_INTERNET |<br>| Legacy Display Name | Internet Explorer |<br>| Legacy Default Path | Not applicable—virtual folder | |
| - **FOLDERID\_Libraries** | | GUID | {1B3EA5DC-B587-4786-B4EF-BD1DC332AEAE} |<br>| --- | --- |<br>| Display Name | Libraries |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Libraries |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_Links** | | GUID | {bfb9d5e0-c6a9-404c-b2b2-ae6db6af4968} |<br>| --- | --- |<br>| Display Name | Links |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Links |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_LocalAppData** | | GUID | {F1B32785-6FBA-4FCF-9D55-7B8E7F157091} |<br>| --- | --- |<br>| Display Name | Local |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA% (%USERPROFILE%\AppData\Local) |<br>| CSIDL Equivalent | CSIDL\_LOCAL\_APPDATA |<br>| Legacy Display Name | Application Data |<br>| Legacy Default Path | %USERPROFILE%\Local Settings\Application Data | |
| - **FOLDERID\_LocalAppDataLow** | | GUID | {A520A1A4-1780-4FF6-BD18-167343C5AF16} |<br>| --- | --- |<br>| Display Name | LocalLow |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\AppData\LocalLow |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_LocalizedResourcesDir** | | GUID | {2A00375E-224C-49DE-B8D1-440DF7EF3DDC} |<br>| --- | --- |<br>| Display Name | None |<br>| Folder Type | FIXED |<br>| Default Path | %windir%\resources\0409 (code page) |<br>| CSIDL Equivalent | CSIDL\_RESOURCES\_LOCALIZED |<br>| Legacy Display Name | None |<br>| Legacy Default Path | %windir%\resources\0409 (code page) | |
| - **FOLDERID\_Music** | | GUID | {4BD8D571-6D19-48D3-BE97-422220080E43} |<br>| --- | --- |<br>| Display Name | Music |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Music |<br>| CSIDL Equivalent | CSIDL\_MYMUSIC |<br>| Legacy Display Name | My Music |<br>| Legacy Default Path | %USERPROFILE%\My Documents\My Music | |
| - **FOLDERID\_MusicLibrary** | | GUID | {2112AB0A-C86A-4FFE-A368-0DE96E47012E} |<br>| --- | --- |<br>| Display Name | Music |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Libraries\Music.library-ms |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_NetHood** | | GUID | {C5ABBF53-E17F-4121-8900-86626FC2C973} |<br>| --- | --- |<br>| Display Name | Network Shortcuts |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Network Shortcuts |<br>| CSIDL Equivalent | CSIDL\_NETHOOD |<br>| Legacy Display Name | NetHood |<br>| Legacy Default Path | %USERPROFILE%\NetHood | |
| - **FOLDERID\_NetworkFolder** | | GUID | {D20BEEC4-5CA8-4905-AE3B-BF251EA09B53} |<br>| --- | --- |<br>| Display Name | Network |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | CSIDL\_NETWORK, CSIDL\_COMPUTERSNEARME |<br>| Legacy Display Name | My Network Places |<br>| Legacy Default Path | Not applicable—virtual folder | |
| - **FOLDERID\_Objects3D** | | GUID | {31C0DD25-9439-4F12-BF41-7FF4EDA38722} |<br>| --- | --- |<br>| Display Name | 3D Objects |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\3D Objects |<br>| CSIDL Equivalent | None, value introduced in Windows 10, version 1703 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_OriginalImages** | | GUID | {2C36C0AA-5812-4b87-BFD0-4CD0DFB19B39} |<br>| --- | --- |<br>| Display Name | Original Images |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows Photo Gallery\Original Images |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_PhotoAlbums** | | GUID | {69D2CF90-FC33-4FB7-9A0C-EBB0F0FCB43C} |<br>| --- | --- |<br>| Display Name | Slide Shows |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Pictures\Slide Shows |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_PicturesLibrary** | | GUID | {A990AE9F-A03B-4E80-94BC-9912D7504104} |<br>| --- | --- |<br>| Display Name | Pictures |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Libraries\Pictures.library-ms |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_Pictures** | | GUID | {33E28130-4E1E-4676-835A-98395C3BC3BB} |<br>| --- | --- |<br>| Display Name | Pictures |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Pictures |<br>| CSIDL Equivalent | CSIDL\_MYPICTURES |<br>| Legacy Display Name | My Pictures |<br>| Legacy Default Path | %USERPROFILE%\My Documents\My Pictures | |
| - **FOLDERID\_Playlists** | | GUID | {DE92C1C7-837F-4F69-A3BB-86E631204A23} |<br>| --- | --- |<br>| Display Name | Playlists |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Music\Playlists |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_PrintersFolder** | | GUID | {76FC4E2D-D6AD-4519-A663-37BD56068185} |<br>| --- | --- |<br>| Display Name | Printers |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | CSIDL\_PRINTERS |<br>| Legacy Display Name | Printers and Faxes |<br>| Legacy Default Path | Not applicable—virtual folder | |
| - **FOLDERID\_PrintHood** | | GUID | {9274BD8D-CFD1-41C3-B35E-B13F55A758F4} |<br>| --- | --- |<br>| Display Name | Printer Shortcuts |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Printer Shortcuts |<br>| CSIDL Equivalent | CSIDL\_PRINTHOOD |<br>| Legacy Display Name | PrintHood |<br>| Legacy Default Path | %USERPROFILE%\PrintHood | |
| - **FOLDERID\_Profile** | | GUID | {5E6C858F-0E22-4760-9AFE-EA3317B67173} |<br>| --- | --- |<br>| Display Name | The user's username (%USERNAME%) |<br>| Folder Type | FIXED |<br>| Default Path | %USERPROFILE% (%SystemDrive%\Users\%USERNAME%) |<br>| CSIDL Equivalent | CSIDL\_PROFILE |<br>| Legacy Display Name | The user's username (%USERNAME%) |<br>| Legacy Default Path | %USERPROFILE% (%SystemDrive%\Documents and Settings\%USERNAME%) | |
| - **FOLDERID\_ProgramData** | | GUID | {62AB5D82-FDC1-4DC3-A9DD-070D1D495D97} |<br>| --- | --- |<br>| Display Name | ProgramData |<br>| Folder Type | FIXED |<br>| Default Path | %ALLUSERSPROFILE% (%ProgramData%, %SystemDrive%\ProgramData) |<br>| CSIDL Equivalent | CSIDL\_COMMON\_APPDATA |<br>| Legacy Display Name | Application Data |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Application Data | |
| - **FOLDERID\_ProgramFiles** | See Remarks for more information.<br><br><br>| GUID | {905e63b6-c1bf-494e-b29c-65b732d3d21a} |<br>| --- | --- |<br>| Display Name | Program Files |<br>| Folder Type | FIXED |<br>| Default Path | %ProgramFiles% (%SystemDrive%\Program Files) |<br>| CSIDL Equivalent | CSIDL\_PROGRAM\_FILES |<br>| Legacy Display Name | Program Files |<br>| Legacy Default Path | %ProgramFiles% (%SystemDrive%\Program Files) | |
| - **FOLDERID\_ProgramFilesX64** | This value is not supported on 32-bit operating systems. It also is not supported for 32-bit applications running on 64-bit operating systems. Attempting to use FOLDERID\_ProgramFilesX64 in either situation results in an error. See Remarks for more information.<br><br><br>| GUID | {6D809377-6AF0-444b-8957-A3773F02200E} |<br>| --- | --- |<br>| Display Name | Program Files |<br>| Folder Type | FIXED |<br>| Default Path | %ProgramFiles% (%SystemDrive%\Program Files) |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Program Files |<br>| Legacy Default Path | %ProgramFiles% (%SystemDrive%\Program Files) | |
| - **FOLDERID\_ProgramFilesX86** | See Remarks for more information.<br><br><br>| GUID | {7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E} |<br>| --- | --- |<br>| Display Name | Program Files |<br>| Folder Type | FIXED |<br>| Default Path | %ProgramFiles% (%SystemDrive%\Program Files) |<br>| CSIDL Equivalent | CSIDL\_PROGRAM\_FILESX86 |<br>| Legacy Display Name | Program Files |<br>| Legacy Default Path | %ProgramFiles% (%SystemDrive%\Program Files) | |
| - **FOLDERID\_ProgramFilesCommon** | See Remarks for more information.<br><br><br>| GUID | {F7F1ED05-9F6D-47A2-AAAE-29D317C6F066} |<br>| --- | --- |<br>| Display Name | Common Files |<br>| Folder Type | FIXED |<br>| Default Path | %ProgramFiles%\Common Files |<br>| CSIDL Equivalent | CSIDL\_PROGRAM\_FILES\_COMMON |<br>| Legacy Display Name | Common Files |<br>| Legacy Default Path | %ProgramFiles%\Common Files | |
| - **FOLDERID\_ProgramFilesCommonX64** | See Remarks for more information.<br><br><br>| GUID | {6365D5A7-0F0D-45E5-87F6-0DA56B6A4F7D} |<br>| --- | --- |<br>| Display Name | Common Files |<br>| Folder Type | FIXED |<br>| Default Path | %ProgramFiles%\Common Files |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Common Files |<br>| Legacy Default Path | %ProgramFiles%\Common Files | |
| - **FOLDERID\_ProgramFilesCommonX86** | See Remarks for more information.<br><br><br>| GUID | {DE974D24-D9C6-4D3E-BF91-F4455120B917} |<br>| --- | --- |<br>| Display Name | Common Files |<br>| Folder Type | FIXED |<br>| Default Path | %ProgramFiles%\Common Files |<br>| CSIDL Equivalent | CSIDL\_PROGRAM\_FILES\_COMMONX86 |<br>| Legacy Display Name | Common Files |<br>| Legacy Default Path | %ProgramFiles%\Common Files | |
| - **FOLDERID\_Programs** | | GUID | {A77F5D77-2E2B-44C3-A6A2-ABA601054A51} |<br>| --- | --- |<br>| Display Name | Programs |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Start Menu\Programs |<br>| CSIDL Equivalent | CSIDL\_PROGRAMS |<br>| Legacy Display Name | Programs |<br>| Legacy Default Path | %USERPROFILE%\Start Menu\Programs | |
| - **FOLDERID\_Public** | | GUID | {DFDF76A2-C82A-4D63-906A-5644AC457385} |<br>| --- | --- |<br>| Display Name | Public |<br>| Folder Type | FIXED |<br>| Default Path | %PUBLIC% (%SystemDrive%\Users\Public) |<br>| CSIDL Equivalent | None, new for Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_PublicDesktop** | | GUID | {C4AA340D-F20F-4863-AFEF-F87EF2E6BA25} |<br>| --- | --- |<br>| Display Name | Public Desktop |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Desktop |<br>| CSIDL Equivalent | CSIDL\_COMMON\_DESKTOPDIRECTORY |<br>| Legacy Display Name | Desktop |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Desktop | |
| - **FOLDERID\_PublicDocuments** | | GUID | {ED4824AF-DCE4-45A8-81E2-FC7965083634} |<br>| --- | --- |<br>| Display Name | Public Documents |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Documents |<br>| CSIDL Equivalent | CSIDL\_COMMON\_DOCUMENTS |<br>| Legacy Display Name | Shared Documents |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Documents | |
| - **FOLDERID\_PublicDownloads** | | GUID | {3D644C9B-1FB8-4f30-9B45-F670235F79C0} |<br>| --- | --- |<br>| Display Name | Public Downloads |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Downloads |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_PublicGameTasks** | | GUID | {DEBF2536-E1A8-4c59-B6A2-414586476AEA} |<br>| --- | --- |<br>| Display Name | GameExplorer |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\Microsoft\Windows\GameExplorer |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_PublicLibraries** | | GUID | {48DAF80B-E6CF-4F4E-B800-0E69D84EE384} |<br>| --- | --- |<br>| Display Name | Libraries |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\Microsoft\Windows\Libraries |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_PublicMusic** | | GUID | {3214FAB5-9757-4298-BB61-92A9DEAA44FF} |<br>| --- | --- |<br>| Display Name | Public Music |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Music |<br>| CSIDL Equivalent | CSIDL\_COMMON\_MUSIC |<br>| Legacy Display Name | Shared Music |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Documents\My Music | |
| - **FOLDERID\_PublicPictures** | | GUID | {B6EBFB86-6907-413C-9AF7-4FC2ABF07CC5} |<br>| --- | --- |<br>| Display Name | Public Pictures |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Pictures |<br>| CSIDL Equivalent | CSIDL\_COMMON\_PICTURES |<br>| Legacy Display Name | Shared Pictures |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Documents\My Pictures | |
| - **FOLDERID\_PublicRingtones** | | GUID | {E555AB60-153B-4D17-9F04-A5FE99FC15EC} |<br>| --- | --- |<br>| Display Name | Ringtones |<br>| Folder Type | COMMON |<br>| Default Path | %ALLUSERSPROFILE%\Microsoft\Windows\Ringtones |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_PublicUserTiles** | | GUID | {0482af6c-08f1-4c34-8c90-e17ec98b1e17} |<br>| --- | --- |<br>| Display Name | Public Account Pictures |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\AccountPictures |<br>| CSIDL Equivalent | None, value introduced in Windows 8 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_PublicVideos** | | GUID | {2400183A-6185-49FB-A2D8-4A392A602BA3} |<br>| --- | --- |<br>| Display Name | Public Videos |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Videos |<br>| CSIDL Equivalent | CSIDL\_COMMON\_VIDEO |<br>| Legacy Display Name | Shared Video |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Documents\My Videos | |
| - **FOLDERID\_QuickLaunch** | | GUID | {52a4f021-7b75-48a9-9f6b-4b87a210bc8f} |<br>| --- | --- |<br>| Display Name | Quick Launch |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Internet Explorer\Quick Launch |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Quick Launch |<br>| Legacy Default Path | %APPDATA%\Microsoft\Internet Explorer\Quick Launch | |
| - **FOLDERID\_Recent** | | GUID | {AE50C081-EBD2-438A-8655-8A092E34987A} |<br>| --- | --- |<br>| Display Name | Recent Items |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Recent |<br>| CSIDL Equivalent | CSIDL\_RECENT |<br>| Legacy Display Name | My Recent Documents |<br>| Legacy Default Path | %USERPROFILE%\Recent | |
| - **FOLDERID\_RecordedTV** | Not used. This value is undefined as of Windows 7. |
| - **FOLDERID\_RecordedTVLibrary** | | GUID | {1A6FDBA2-F42D-4358-A798-B74D745926C5} |<br>| --- | --- |<br>| Display Name | Recorded TV |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\RecordedTV.library-ms |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_RecycleBinFolder** | | GUID | {B7534046-3ECB-4C18-BE4E-64CD4CB7D6AC} |<br>| --- | --- |<br>| Display Name | Recycle Bin |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | CSIDL\_BITBUCKET |<br>| Legacy Display Name | Recycle Bin |<br>| Legacy Default Path | Not applicable—virtual folder | |
| - **FOLDERID\_ResourceDir** | | GUID | {8AD10C31-2ADB-4296-A8F7-E4701232C972} |<br>| --- | --- |<br>| Display Name | Resources |<br>| Folder Type | FIXED |<br>| Default Path | %windir%\Resources |<br>| CSIDL Equivalent | CSIDL\_RESOURCES |<br>| Legacy Display Name | Resources |<br>| Legacy Default Path | %windir%\Resources | |
| - **FOLDERID\_Ringtones** | | GUID | {C870044B-F49E-4126-A9C3-B52A1FF411E8} |<br>| --- | --- |<br>| Display Name | Ringtones |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\Ringtones |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_RoamingAppData** | | GUID | {3EB685DB-65F9-4CF6-A03A-E3EF65729F3D} |<br>| --- | --- |<br>| Display Name | Roaming |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA% (%USERPROFILE%\AppData\Roaming) |<br>| CSIDL Equivalent | CSIDL\_APPDATA |<br>| Legacy Display Name | Application Data |<br>| Legacy Default Path | %APPDATA% (%USERPROFILE%\Application Data) | |
| - **FOLDERID\_RoamedTileImages** | | GUID | {AAA8D5A5-F1D6-4259-BAA8-78E7EF60835E} |<br>| --- | --- |<br>| Display Name | RoamedTileImages |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\RoamedTileImages |<br>| CSIDL Equivalent | None, value introduced in Windows 8 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_RoamingTiles** | | GUID | {00BCFC5A-ED94-4e48-96A1-3F6217F21990} |<br>| --- | --- |<br>| Display Name | RoamingTiles |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\RoamingTiles |<br>| CSIDL Equivalent | None, value introduced in Windows 8 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SampleMusic** | | GUID | {B250C668-F57D-4EE1-A63C-290EE7D1AA1F} |<br>| --- | --- |<br>| Display Name | Sample Music |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Music\Sample Music |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Sample Music |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Documents\My Music\Sample Music | |
| - **FOLDERID\_SamplePictures** | | GUID | {C4900540-2379-4C75-844B-64E6FAF8716B} |<br>| --- | --- |<br>| Display Name | Sample Pictures |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Pictures\Sample Pictures |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Sample Pictures |<br>| Legacy Default Path | %ALLUSERSPROFILE%\Documents\My Pictures\Sample Pictures | |
| - **FOLDERID\_SamplePlaylists** | | GUID | {15CA69B3-30EE-49C1-ACE1-6B5EC372AFB5} |<br>| --- | --- |<br>| Display Name | Sample Playlists |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Music\Sample Playlists |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SampleVideos** | | GUID | {859EAD94-2E85-48AD-A71A-0969CB56A6CD} |<br>| --- | --- |<br>| Display Name | Sample Videos |<br>| Folder Type | COMMON |<br>| Default Path | %PUBLIC%\Videos\Sample Videos |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SavedGames** | | GUID | {4C5C32FF-BB9D-43b0-B5B4-2D72E54EAAA4} |<br>| --- | --- |<br>| Display Name | Saved Games |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Saved Games |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SavedPictures** | | GUID | {3B193882-D3AD-4eab-965A-69829D1FB59F} |<br>| --- | --- |<br>| Display Name | Saved Pictures |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Pictures\Saved Pictures |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SavedPicturesLibrary** | | GUID | {E25B5812-BE88-4bd9-94B0-29233477B6C3} |<br>| --- | --- |<br>| Display Name | Saved Pictures Library |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Libraries\SavedPictures.library-ms |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SavedSearches** | | GUID | {7d1d3a04-debb-4115-95cf-2f29da2920da} |<br>| --- | --- |<br>| Display Name | Searches |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Searches |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_Screenshots** | | GUID | {b7bede81-df94-4682-a7d8-57a52620b86f} |<br>| --- | --- |<br>| Display Name | Screenshots |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Pictures\Screenshots |<br>| CSIDL Equivalent | None, value introduced in Windows 8 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SEARCH\_CSC** | | GUID | {ee32e446-31ca-4aba-814f-a5ebd2fd6d5e} |<br>| --- | --- |<br>| Display Name | Offline Files |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SearchHistory** | | GUID | {0D4C3DB6-03A3-462F-A0E6-08924C41B5D4} |<br>| --- | --- |<br>| Display Name | History |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\ConnectedSearch\History |<br>| CSIDL Equivalent | None, value introduced in Windows 8.1 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SearchHome** | | GUID | {190337d1-b8ca-4121-a639-6d472d16972a} |<br>| --- | --- |<br>| Display Name | Search Results |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SEARCH\_MAPI** | | GUID | {98ec0e18-2098-4d44-8644-66979315a281} |<br>| --- | --- |<br>| Display Name | Microsoft Office Outlook |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SearchTemplates** | | GUID | {7E636BFE-DFA9-4D5E-B456-D7B39851D8A9} |<br>| --- | --- |<br>| Display Name | Templates |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows\ConnectedSearch\Templates |<br>| CSIDL Equivalent | None, value introduced in Windows 8.1 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SendTo** | | GUID | {8983036C-27C0-404B-8F08-102D10DCFD74} |<br>| --- | --- |<br>| Display Name | SendTo |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\SendTo |<br>| CSIDL Equivalent | CSIDL\_SENDTO |<br>| Legacy Display Name | SendTo |<br>| Legacy Default Path | %USERPROFILE%\SendTo | |
| - **FOLDERID\_SidebarDefaultParts** | | GUID | {7B396E54-9EC5-4300-BE0A-2482EBAE1A26} |<br>| --- | --- |<br>| Display Name | Gadgets |<br>| Folder Type | COMMON |<br>| Default Path | %ProgramFiles%\Windows Sidebar\Gadgets |<br>| CSIDL Equivalent | None, new for Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SidebarParts** | | GUID | {A75D362E-50FC-4fb7-AC2C-A8BEAA314493} |<br>| --- | --- |<br>| Display Name | Gadgets |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Microsoft\Windows Sidebar\Gadgets |<br>| CSIDL Equivalent | None, new for Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SkyDrive** | | GUID | {A52BBA46-E9E1-435f-B3D9-28DAA648C0F6} |<br>| --- | --- |<br>| Display Name | OneDrive |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\OneDrive |<br>| CSIDL Equivalent | None, value introduced in Windows 8.1 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SkyDriveCameraRoll** | | GUID | {767E6811-49CB-4273-87C2-20F355E1085B} |<br>| --- | --- |<br>| Display Name | Camera Roll |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\OneDrive\Pictures\Camera Roll |<br>| CSIDL Equivalent | None, value introduced in Windows 8.1 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SkyDriveDocuments** | | GUID | {24D89E24-2F19-4534-9DDE-6A6671FBB8FE} |<br>| --- | --- |<br>| Display Name | Documents |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\OneDrive\Documents |<br>| CSIDL Equivalent | None, value introduced in Windows 8.1 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SkyDrivePictures** | | GUID | {339719B5-8C47-4894-94C2-D8F77ADD44A6} |<br>| --- | --- |<br>| Display Name | Pictures |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\OneDrive\Pictures |<br>| CSIDL Equivalent | None, value introduced in Windows 8.1 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_StartMenu** | | GUID | {625B53C3-AB48-4EC1-BA1F-A1EF4146FC19} |<br>| --- | --- |<br>| Display Name | Start Menu |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Start Menu |<br>| CSIDL Equivalent | CSIDL\_STARTMENU |<br>| Legacy Display Name | Start Menu |<br>| Legacy Default Path | %USERPROFILE%\Start Menu | |
| - **FOLDERID\_Startup** | | GUID | {B97D20BB-F46A-4C97-BA10-5E3608430854} |<br>| --- | --- |<br>| Display Name | Startup |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Start Menu\Programs\StartUp |<br>| CSIDL Equivalent | CSIDL\_STARTUP, CSIDL\_ALTSTARTUP |<br>| Legacy Display Name | Startup |<br>| Legacy Default Path | %USERPROFILE%\Start Menu\Programs\StartUp | |
| - **FOLDERID\_SyncManagerFolder** | | GUID | {43668BF8-C14E-49B2-97C9-747784D784B7} |<br>| --- | --- |<br>| Display Name | Sync Center |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SyncResultsFolder** | | GUID | {289a9a43-be44-4057-a41b-587a76d7e7f9} |<br>| --- | --- |<br>| Display Name | Sync Results |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_SyncSetupFolder** | | GUID | {0F214138-B1D3-4a90-BBA9-27CBC0C5389A} |<br>| --- | --- |<br>| Display Name | Sync Setup |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None, value introduced in Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_System** | | GUID | {1AC14E77-02E7-4E5D-B744-2EB1AE5198B7} |<br>| --- | --- |<br>| Display Name | System32 |<br>| Folder Type | FIXED |<br>| Default Path | %windir%\system32 |<br>| CSIDL Equivalent | CSIDL\_SYSTEM |<br>| Legacy Display Name | system32 |<br>| Legacy Default Path | %windir%\system32 | |
| - **FOLDERID\_SystemX86** | | GUID | {D65231B0-B2F1-4857-A4CE-A8E7C6EA7D27} |<br>| --- | --- |<br>| Display Name | System32 |<br>| Folder Type | FIXED |<br>| Default Path | %windir%\system32 |<br>| CSIDL Equivalent | CSIDL\_SYSTEMX86 |<br>| Legacy Display Name | system32 |<br>| Legacy Default Path | %windir%\system32 | |
| - **FOLDERID\_Templates** | | GUID | {A63293E8-664E-48DB-A079-DF759E0509F7} |<br>| --- | --- |<br>| Display Name | Templates |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Templates |<br>| CSIDL Equivalent | CSIDL\_TEMPLATES |<br>| Legacy Display Name | Templates |<br>| Legacy Default Path | %USERPROFILE%\Templates | |
| - **FOLDERID\_TreeProperties** | Not used in Windows Vista. Unsupported as of Windows 7. |
| - **FOLDERID\_UserPinned** | | GUID | {9E3995AB-1F9C-4F13-B827-48B24B6C7174} |<br>| --- | --- |<br>| Display Name | User Pinned |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Internet Explorer\Quick Launch\User Pinned |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_UserProfiles** | | GUID | {0762D272-C50A-4BB0-A382-697DCD729B80} |<br>| --- | --- |<br>| Display Name | Users |<br>| Folder Type | FIXED |<br>| Default Path | %SystemDrive%\Users |<br>| CSIDL Equivalent | None, new for Windows Vista |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_UserProgramFiles** | | GUID | {5CD7AEE2-2219-4A67-B85D-6C9CE15660CB} |<br>| --- | --- |<br>| Display Name | Programs |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Programs |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_UserProgramFilesCommon** | | GUID | {BCBD3057-CA5C-4622-B42D-BC56DB0AE516} |<br>| --- | --- |<br>| Display Name | Programs |<br>| Folder Type | PERUSER |<br>| Default Path | %LOCALAPPDATA%\Programs\Common |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_UsersFiles** | | GUID | {f3ce0f7c-4901-4acc-8648-d5d44b04ef8f} |<br>| --- | --- |<br>| Display Name | The user's full name (for instance, Jean Philippe Bagel) entered when the user account was created. |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_UsersLibraries** | | GUID | {A302545D-DEFF-464b-ABE8-61C8648D939B} |<br>| --- | --- |<br>| Display Name | Libraries |<br>| Folder Type | VIRTUAL |<br>| Default Path | Not applicable—virtual folder |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_Videos** | | GUID | {18989B1D-99B5-455B-841C-AB7C74E4DDFC} |<br>| --- | --- |<br>| Display Name | Videos |<br>| Folder Type | PERUSER |<br>| Default Path | %USERPROFILE%\Videos |<br>| CSIDL | CSIDL\_MYVIDEO |<br>| Legacy Display Name | My Videos |<br>| Legacy Default Path | %USERPROFILE%\My Documents\My Videos | |
| - **FOLDERID\_VideosLibrary** | | GUID | {491E922F-5643-4AF4-A7EB-4E7A138D8174} |<br>| --- | --- |<br>| Display Name | Videos |<br>| Folder Type | PERUSER |<br>| Default Path | %APPDATA%\Microsoft\Windows\Libraries\Videos.library-ms |<br>| CSIDL Equivalent | None, value introduced in Windows 7 |<br>| Legacy Display Name | Not applicable |<br>| Legacy Default Path | Not applicable | |
| - **FOLDERID\_Windows** | | GUID | {F38BF404-1D43-42F2-9305-67DE0B28FC23} |<br>| --- | --- |<br>| Display Name | Windows |<br>| Folder Type | FIXED |<br>| Default Path | %windir% |<br>| CSIDL Equivalent | CSIDL\_WINDOWS |<br>| Legacy Display Name | WINDOWS |<br>| Legacy Default Path | %windir% | |

## Remarks

The interpretation of certain **KNOWNFOLDERID** values depends on whether the folder is part of a 32-bit or 64-bit application and whether that application is running on a 32-bit or 64-bit operating system. If your application needs to distinguish between, for example, **Program Files** and **Program Files (x86)**, you must use the right **KNOWNFOLDERID** for the situation.

The following tables summarize the **KNOWNFOLDERID** use in those cases.

**FOLDERID\_ProgramFiles**

| Operating System | Application | KNOWNFOLDERID | Default Path | CSIDL Equivalent |
| --- | --- | --- | --- | --- |
| 32 bit | 32 bit | FOLDERID\_ProgramFiles | %SystemDrive%\Program Files | CSIDL\_PROGRAM\_FILES |
| 32 bit | 32 bit | FOLDERID\_ProgramFilesX86 | %SystemDrive%\Program Files | CSIDL\_PROGRAM\_FILESX86 |
| 32 bit | 32 bit | FOLDERID\_ProgramFilesX64 (not supported under 32-bit operating systems) | Not applicable | Not applicable |
| 64 bit | 64 bit | FOLDERID\_ProgramFiles | %SystemDrive%\Program Files | CSIDL\_PROGRAM\_FILES |
| 64 bit | 64 bit | FOLDERID\_ProgramFilesX86 | %SystemDrive%\Program Files (x86) | CSIDL\_PROGRAM\_FILESX86 |
| 64 bit | 64 bit | FOLDERID\_ProgramFilesX64 | %SystemDrive%\Program Files | None |
| 64 bit | 32 bit | FOLDERID\_ProgramFiles | %SystemDrive%\Program Files (x86) | CSIDL\_PROGRAM\_FILES |
| 64 bit | 32 bit | FOLDERID\_ProgramFilesX86 | %SystemDrive%\Program Files (x86) | CSIDL\_PROGRAM\_FILESX86 |
| 64 bit | 32 bit | FOLDERID\_ProgramFilesX64 (not supported for 32-bit applications) | Not applicable | Not applicable |

**FOLDERID\_ProgramFilesCommon**

| Operating System | Application | KNOWNFOLDERID | Default Path | CSIDL Equivalent |
| --- | --- | --- | --- | --- |
| 32 bit | 32 bit | FOLDERID\_ProgramFilesCommon | %ProgramFiles%\Common Files | CSIDL\_PROGRAM\_FILES\_COMMON |
| 32 bit | 32 bit | FOLDERID\_ProgramFilesCommonX86 | %ProgramFiles%\Common Files | CSIDL\_PROGRAM\_FILES\_COMMONX86 |
| 32 bit | 32 bit | FOLDERID\_ProgramFilesCommonX64 (undefined) | Not applicable | Not applicable |
| 64 bit | 64 bit | FOLDERID\_ProgramFilesCommon | %ProgramFiles%\Common Files | CSIDL\_PROGRAM\_FILES\_COMMON |
| 64 bit | 64 bit | FOLDERID\_ProgramFilesCommonX86 | %ProgramFiles(x86)%\Common Files | CSIDL\_PROGRAM\_FILES\_COMMONX86 |
| 64 bit | 64 bit | FOLDERID\_ProgramFilesCommonX64 | %ProgramFiles%\Common Files | None |
| 64 bit | 32 bit | FOLDERID\_ProgramFilesCommon | %ProgramFiles(x86)%\Common Files | CSIDL\_PROGRAM\_FILES\_COMMON |
| 64 bit | 32 bit | FOLDERID\_ProgramFilesCommonX86 | %ProgramFiles(x86)%\Common Files | CSIDL\_PROGRAM\_FILES\_COMMONX86 |
| 64 bit | 32 bit | FOLDERID\_ProgramFilesCommonX64 | %ProgramFiles%\Common Files | None |

**FOLDERID\_System**

| Operating System | Application | KNOWNFOLDERID | Default Path | CSIDL Equivalent |
| --- | --- | --- | --- | --- |
| 32 bit | 32 bit | FOLDERID\_System | %windir%\system32 | CSIDL\_SYSTEM |
| 32 bit | 32 bit | FOLDERID\_SystemX86 | %windir%\system32 | CSIDL\_SYSTEMX86 |
| 64 bit | 64 bit | FOLDERID\_System | %windir%\system32 | CSIDL\_SYSTEM |
| 64 bit | 64 bit | FOLDERID\_SystemX86 | %windir%\syswow64 | CSIDL\_SYSTEMX86 |
| 64 bit | 32 bit | FOLDERID\_System | %windir%\system32 | CSIDL\_SYSTEM |
| 64 bit | 32 bit | FOLDERID\_SystemX86 | %windir%\syswow64 | CSIDL\_SYSTEMX86 |

We have used environment strings to provide generic paths throughout this topic. The following tables give examples of the paths those environment strings represent. In some cases, these paths might not match those on a particular computer because of choices made during installation or later folder redirection. Note that some paths have changed for Windows Vista.

**Windows Vista and later**

| Environment String | Example Path |
| --- | --- |
| %ALLUSERSPROFILE% | C:\ProgramData |
| %APPDATA% | C:\Users\*username*\AppData\Roaming |
| %LOCALAPPDATA% | C:\Users\*username*\AppData\Local |
| %ProgramData% | C:\ProgramData |
| %ProgramFiles% | C:\Program Files |
| %ProgramFiles(x86)% | C:\Program Files (x86) |
| %PUBLIC% | C:\Users\Public |
| %SystemDrive% | C: |
| %USERPROFILE% | C:\Users\*username* |
| %windir% | C:\Windows |

**Windows XP and earlier**

| Environment String | Example Path |
| --- | --- |
| %ALLUSERSPROFILE% | C:\Documents and Settings\All Users |
| %APPDATA% | C:\Documents and Settings\*username*\Application Data |
| %ProgramFiles% | C:\Program Files |
| %SystemDrive% | C: |
| %USERPROFILE% | C:\Documents and Settings\*username* |
| %windir% | C:\Windows |

## Requirements

| Requirement | Value |
| --- | --- |
| Header | - Knownfolders.h |