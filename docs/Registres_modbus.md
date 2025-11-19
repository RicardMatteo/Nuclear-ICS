# **MBANS – Documentation des registres Modbus**

Ce document présente l’ensemble des registres Modbus utilisés par le simulateur Asherah (MBANS).
Il s’appuie sur l’annexe fournie dans la documentation officielle (Modbus Asherah – Deployment Guide, 2023).

MBANS expose **4 catégories Modbus** :

| Type de registre      | Accès            | Taille  | Usage                                                     |
| --------------------- | ---------------- | ------- | --------------------------------------------------------- |
| **Coils**             | lecture/écriture | 1 bit   | Commandes (pompes, vannes, SCRAM…)                        |
| **Discrete Inputs**   | lecture seule    | 1 bit   | États réels du système                                    |
| **Holding Registers** | lecture/écriture | 16 bits | Setpoints et commandes analogiques                        |
| **Input Registers**   | lecture seule    | 16 bits | Mesures physiques du réacteur et des systèmes auxiliaires |

---

# **1. Coils (Read/Write – 1 bit)**

Commandes envoyées au simulateur (pompes, vannes, SCRAM…).

| Adresse | Tag                   | Valeur nominale | Commentaire           |
| ------- | --------------------- | --------------- | --------------------- |
| 00000   | RC1_PumpOnOffCmd      | 1               |                       |
| 00001   | RC2_PumpOnOffCmd      | 1               |                       |
| 00002   | CR_SCRAMCmd           | 0               | Commande SCRAM        |
| 00003   | PZ_BackupHeaterPowCmd | 0               |                       |
| 00004   | AF_MakeupPumpCmd      | 1               |                       |
| 00005   | SD_SafetyValveCmd     | 0               |                       |
| 00006   | TB_IsoValveCmd        | 1               |                       |
| 00007   | CC_PumpOnOffCmd       | 1               |                       |
| 00008   | FW_Pump1OnOffCmd      | 1               |                       |
| 00009   | FW_Pump2OnOffCmd      | 1               |                       |
| 00010   | FW_Pump3OnOffCmd      | 0               |                       |
| 00011   | CE_Pump1OnOffCmd      | 1               |                       |
| 00012   | CE_Pump2OnOffCmd      | 1               |                       |
| 00013   | CE_Pump3OnOffCmd      | 0               |                       |
| 00014   | INT_SimulationStopCmd | 0               | *1 = stop simulation* |

---

# **2. Discrete Inputs (Read Only – 1 bit)**

Retour d’état des composants physiques.

| Adresse | Tag                | Valeur nominale | Commentaire                |
| ------- | ------------------ | --------------- | -------------------------- |
| 00000   | CR_SCRAM           | 0               | Confirmation SCRAM         |
| 00001   | AF_MakeupPumpOnOff | 1               |                            |
| 00002   | SD_SafetyValvePos  | 0               |                            |
| 00003   | TB_IsoValvePos     | 1               |                            |
| 00004   | GN_GenBreak        | 1               | 1 = normal, 0 = déconnecté |
| 00005   | CC_PumpOnOff       | 1               |                            |
| 00006   | FW_Pump1OnOff      | 1               |                            |
| 00007   | FW_Pump2OnOff      | 1               |                            |
| 00008   | FW_Pump3OnOff      | 0               |                            |
| 00009   | CE_Pump1OnOff      | 1               |                            |
| 00010   | CE_Pump2OnOff      | 1               |                            |
| 00011   | CE_Pump3OnOff      | 0               |                            |

---

# **3. Holding Registers (Read/Write – 16 bits)**

Valeurs analogiques écrites par le SCADA ou générées par les contrôleurs (vannes, setpoints, vitesses…).

> **Important :** toutes les valeurs sont converties en **uint16** selon l’échelle Min/Max.

| Addr        | Tag                      | Valeur | Min | Max  | Unité | Commentaire                   |
| ----------- | ------------------------ | ------ | --- | ---- | ----- | ----------------------------- |
| 00000       | RC1_PumpSpeedCmd         | 100    | 0   | 100  | %     | Généré par le contrôleur      |
| 00001       | RC2_PumpSpeedCmd         | 100    | 0   | 100  | %     |                               |
| 00002       | CR_PosCmd                | 833    | 0   | 1000 | step  |                               |
| 00003       | PZ_MainHeaterPowCmd      | 0      | 0   | 100  | %     |                               |
| 00004       | PZ_CL1SprayValveCmd      | 0      | 0   | 100  | %     |                               |
| 00005       | PZ_CL2SprayValveCmd      | 0      | 0   | 100  | %     |                               |
| 00006       | AF_MakeupValveCmd        | 0      | 0   | 100  | %     |                               |
| 00007       | AF_LetdownValveCmd       | 0      | 0   | 100  | %     |                               |
| 00008       | SD_CtrlValveCmd          | 0      | 0   | 100  | %     |                               |
| 00009       | TB_SpeedCtrlValveCmd     | 100    | 0   | 100  | %     |                               |
| 00010       | CC_PumpSpeedCmd          | 100    | 0   | 100  | %     |                               |
| 00011       | FW_Pump1SpeedCmd         | 100    | 0   | 100  | %     |                               |
| 00012       | FW_Pump2SpeedCmd         | 100    | 0   | 100  | %     |                               |
| 00013       | FW_Pump3SpeedCmd         | 0      | 0   | 100  | %     |                               |
| 00014       | CE_Pump1SpeedCmd         | 100    | 0   | 100  | %     |                               |
| 00015       | CE_Pump2SpeedCmd         | 100    | 0   | 100  | %     |                               |
| 00016       | CE_Pump3SpeedCmd         | 0      | 0   | 100  | %     |                               |
| **00017**   | **CTRL_RXPowerSetpoint** | 100    | 0   | 110  | %     | **Setpoint envoyé par SCADA** |
| **00018**   | **CTRL_PZPressSetPoint** | 15.106 | 0   | 18   | MPa   | **Setpoint envoyé par SCADA** |
| 00019–00030 | Divers placeholders      | 0      | 0   | 0    | -     | Non implémentés               |


# **Tableau 4 — Input Registers (Lecture seule, 16 bits)**

Mesures physiques du réacteur et des systèmes.

| Adresse | Tag                  | Valeur nominale | Min   | Max   | Unité | Commentaire      |
| ------- | -------------------- | --------------- | ----- | ----- | ----- | ---------------- |
| 00000   | RC1_PumpDiffPress    | 1.051           | 0     | 5     | MPa   |                  |
| 00001   | RC1_PumpSpeed        | 100             | 0     | 100   | %     |                  |
| 00002   | RC1_PumpFlow         | 8206.6          | 0     | 10000 | kg/s  |                  |
| 00003   | RC1_PumpTemp         | 338.15          | 0     | 1000  | K     |                  |
| 00004   | RC2_PumpDiffPress    | 1.051           | 0     | 5     | MPa   |                  |
| 00005   | RC2_PumpSpeed        | 100             | 0     | 100   | %     |                  |
| 00006   | RC2_PumpFlow         | 8206.6          | 0     | 10000 | kg/s  |                  |
| 00007   | RC2_PumpTemp         | 338.15          | 0     | 1000  | K     |                  |
| 00008   | RX_MeanCoolTemp      | 576.75          | 0     | 1000  | K     |                  |
| 00009   | RX_InCoolTemp        | 562.94          | 0     | 1000  | K     |                  |
| 00010   | RX_OutCoolTemp       | 590.62          | 0     | 1000  | K     |                  |
| 00011   | RX_CladTemp          | 948.28          | 0     | 1000  | K     |                  |
| 00012   | RX_FuelTemp          | 948.28          | 0     | 1000  | K     |                  |
| 00013   | RX_TotalReac         | 6.1835E-06      | -1e-5 | 1e-5  | $     | Réactivité       |
| 00014   | RX_ReactorPower      | 100             | 0     | 120   | %     | 100% = 2772 MWt  |
| 00015   | RX_ReactorPress      | 15.166          | 0     | 20    | MPa   |                  |
| 00016   | RX_CL1Press          | 15.365          | 0     | 20    | MPa   |                  |
| 00017   | RX_CL2Press          | 15.365          | 0     | 20    | MPa   |                  |
| 00018   | RX_CL1Flow           | 8801.4          | 0     | 10000 | kg/s  |                  |
| 00019   | RX_CL2Flow           | 8801.4          | 0     | 10000 | kg/s  |                  |
| 00020   | CR_Position          | 833             | 0     | 1000  | step  |                  |
| 00021   | PZ_Press             | 15.106          | 0     | 20    | MPa   |                  |
| 00022   | PZ_Temp              | 586.95          | 0     | 1000  | K     |                  |
| 00023   | PZ_Level             | 6               | 0     | 10    | m     |                  |
| 00024   | SG1_InletTemp        | 590.48          | 0     | 1000  | K     |                  |
| 00025   | SG1_OutletTemp       | 562.9           | 0     | 1000  | K     |                  |
| 00026   | SG2_InletTemp        | 590.48          | 0     | 1000  | K     |                  |
| 00027   | SG2_OutletTemp       | 562.9           | 0     | 1000  | K     |                  |
| 00028   | AF_MakeupValvePos    | 0               | 0     | 100   | %     |                  |
| 00029   | AF_LetdownValvePos   | 0               | 0     | 100   | %     |                  |
| 00030   | AF_MakeupFlow        | 0               | 0     | 1000  | kg/s  |                  |
| 00031   | AF_LetdownFlow       | 0               | 0     | 1000  | kg/s  |                  |
| 00032   | SG1_InletWaterTemp   | 495.77          | 0     | 1000  | K     |                  |
| 00033   | SG1_OutletSteamTemp  | 553.08          | 0     | 1000  | K     |                  |
| 00034   | SG1_InletWaterFlow   | 745.14          | 0     | 1000  | kg/s  |                  |
| 00035   | SG1_OutletSteamFlow  | 745.14          | 0     | 1000  | kg/s  |                  |
| 00036   | SG1_WaterTemp        | 553.08          | 0     | 1000  | K     |                  |
| 00037   | SG1_SteamTemp        | 553.08          | 0     | 1000  | K     |                  |
| 00038   | SG1_Press            | 6.41            | 0     | 20    | MPa   |                  |
| 00039   | SG1_Level            | 15              | 0     | 20    | m     |                  |
| 00040   | SG2_InletWaterTemp   | 495.77          | 0     | 1000  | K     |                  |
| 00041   | SG2_OutletSteamTemp  | 553.08          | 0     | 1000  | K     |                  |
| 00042   | SG2_InletWaterFlow   | 745.14          | 0     | 1000  | kg/s  |                  |
| 00043   | SG2_OutletSteamFlow  | 745.14          | 0     | 1000  | kg/s  |                  |
| 00044   | SG2_WaterTemp        | 553.08          | 0     | 1000  | K     |                  |
| 00045   | SG2_SteamTemp        | 553.08          | 0     | 1000  | K     |                  |
| 00046   | SG2_Press            | 6.41            | 0     | 20    | MPa   |                  |
| 00047   | SG2_Level            | 15              | 0     | 20    | m     |                  |
| 00048   | SD_CtrlValvePos      | 0               | 0     | 100   | %     |                  |
| 00049   | TB_Speed             | 157.08          | 0     | 250   | rad/s |                  |
| 00050   | TB_InSteamPress      | 6.41            | 0     | 20    | MPa   |                  |
| 00051   | TB_OutSteamPress     | 5200            | 0     | 10000 | Pa    |                  |
| 00052   | TB_SpeedCtrlValvePos | 100             | 0     | 100   | %     |                  |
| 00053   | TB_InSteamFlow       | 1490.28         | 0     | 2000  | kg/s  |                  |
| 00054   | GN_GenElecPow        | 789             | 0     | 1000  | MW    |                  |
| 00055   | GN_GridFreq          | 50              | 0     | 100   | Hz    |                  |
| 00056   | GN_GenFreq           | 50              | 0     | 100   | Hz    |                  |
| 00057   | CD_Level             | 1               | 0     | 2     | m     |                  |
| 00058   | CD_SteamTemp         | 306.46          | 0     | 1000  | K     |                  |
| 00059   | CD_CondTemp          | 306.46          | 0     | 1000  | K     |                  |
| 00060   | CD_Press             | 5200            | 0     | 10000 | Pa    |                  |
| 00061   | CD_InSteamFlow       | 1490.28         | 0     | 2000  | kg/s  |                  |
| 00062   | CD_OutCondFlow       | 1490.28         | 0     | 2000  | kg/s  |                  |
| 00063   | CC_PumpInletTemp     | 298.15          | 0     | 1000  | K     |                  |
| 00064   | CC_PumpOutletTemp    | 302.48          | 0     | 1000  | K     |                  |
| 00065   | CC_PumpSpeed         | 100             | 0     | 100   | %     |                  |
| 00066   | CC_PumpFlow          | 1.73e5          | 0     | 2e5   | kg/s  |                  |
| 00067   | CC_PumpTemp          | 338.15          | 0     | 1000  | K     |                  |
| 00068   | FW_TankPress         | 1               | 0     | 2     | MPa   |                  |
| 00069   | FW_TankLevel         | 4               | 0     | 10    | m     |                  |
| 00070   | FW_Pump1DiffPress    | 5.41            | 0     | 20    | MPa   |                  |
| 00071   | FW_Pump1Flow         | 745.14          | 0     | 1000  | kg/s  |                  |
| 00072   | FW_Pump1Speed        | 100             | 0     | 120   | %     |                  |
| 00073   | FW_Pump1Temp         | 343.15          | 0     | 1000  | K     |                  |
| 00074   | FW_Pump2DiffPress    | 5.41            | 0     | 20    | MPa   |                  |
| 00075   | FW_Pump2Flow         | 745.14          | 0     | 1000  | kg/s  |                  |
| 00076   | FW_Pump2Speed        | 100             | 0     | 120   | %     |                  |
| 00077   | FW_Pump2Temp         | 343.15          | 0     | 1000  | K     |                  |
| 00078   | FW_Pump3DiffPress    | 5.41            | 0     | 20    | MPa   |                  |
| 00079   | FW_Pump3Flow         | 0               | 0     | 1000  | kg/s  |                  |
| 00080   | FW_Pump3Speed        | 0               | 0     | 120   | %     |                  |
| 00081   | FW_Pump3Temp         | 343.15          | 0     | 1000  | K     |                  |
| 00082   | CE_Pump1DiffPress    | 0.9948          | 0     | 20    | MPa   |                  |
| 00083   | CE_Pump1Speed        | 100             | 0     | 120   | %     |                  |
| 00084   | CE_Pump1Flow         | 745.14          | 0     | 1000  | kg/s  |                  |
| 00085   | CE_Pump1Temp         | 343.15          | 0     | 1000  | K     |                  |
| 00086   | CE_Pump2DiffPress    | 0.9948          | 0     | 20    | MPa   |                  |
| 00087   | CE_Pump2Speed        | 100             | 0     | 120   | %     |                  |
| 00088   | CE_Pump2Flow         | 745.14          | 0     | 1000  | kg/s  |                  |
| 00089   | CE_Pump2Temp         | 343.15          | 0     | 1000  | K     |                  |
| 00090   | CE_Pump3DiffPress    | 0.9948          | 0     | 20    | MPa   |                  |
| 00091   | CE_Pump3Speed        | 0               | 0     | 120   | %     |                  |
| 00092   | CE_Pump3Flow         | 0               | 0     | 1000  | kg/s  |                  |
| 00093   | CE_Pump3Temp         | 343.15          | 0     | 1000  | K     |                  |
| 00094   | INT_SimulationTime   | 0               | 0     | 65535 | s     | Temps simulation |