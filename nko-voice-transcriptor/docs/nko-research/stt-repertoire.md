# Répertoire d’applications Speech-to-Text (voix vers texte)

> Recherche mise à jour le **17 juillet 2026**. Cette liste privilégie les applications utilisables directement, puis les projets open source, services web et API. Elle est volontairement large, mais ne peut pas garantir de recenser absolument tous les projets existants. Les prix, licences, plateformes et politiques de confidentialité peuvent changer : vérifiez-les avant installation ou envoi d’audio sensible.

## Sommaire

1. [Dictée open source](#1-dictée-open-source--parler-et-écrire-dans-lapplication-active)
2. [Transcription open source](#2-applications-open-source-pour-fichiers-audiovidéo-sous-titres-et-réunions)
3. [Dictée commerciale et fonctions natives](#3-applications-et-services-commerciaux-de-dictée)
4. [Transcription web](#4-transcription-web-interviews-podcasts-et-création-de-contenu)
5. [Réunions et visioconférences](#5-réunions-visioconférences-et-prise-de-notes-automatique)
6. [Moteurs, bibliothèques et API](#6-moteurs-bibliothèques-et-api-pour-construire-sa-propre-application)
7. [Projets GitLab](#7-projets-gitlab)
8. [Outils complémentaires et datasets](#8-outils-complémentaires-et-datasets)
9. [Répertoires à surveiller](#9-répertoires-et-pages-de-découverte-à-surveiller)

## Choix rapides

- **Dictée locale, gratuite et multiplateforme :** [Handy](https://github.com/cjpais/Handy)
- **Dictée locale/hybride multiplateforme :** [OpenWhispr](https://github.com/OpenWhispr/openwhispr)
- **Transcrire des fichiers hors ligne :** [Buzz](https://github.com/chidiwilliams/buzz) ou [Vibe](https://github.com/thewh1teagle/vibe)
- **macOS, dictée locale :** [VoiceInk](https://github.com/Beingpax/VoiceInk), [FluidVoice](https://github.com/altic-dev/FluidVoice) ou [OpenSuperWhisper](https://github.com/Starmel/OpenSuperWhisper)
- **Windows, dictée locale :** [OmniDictate](https://github.com/gurjar1/OmniDictate) ou [Chirp](https://github.com/Whamp/chirp-stt)
- **Linux, dictée locale :** [nerd-dictation](https://github.com/ideasman42/nerd-dictation), [Vocalinux](https://github.com/jatinkrmalik/vocalinux) ou [VoxType](https://github.com/peteonrails/voxtype)
- **Android hors ligne :** [Whisper IME](https://github.com/woheller69/whisperIME) ou [Transcribro](https://github.com/soupslurpr/Transcribro)
- **iPhone/iPad hors ligne :** [WhisperBoard](https://github.com/Saik0s/Whisperboard)
- **Réunions et collaboration :** [Otter.ai](https://otter.ai/), [Fireflies.ai](https://fireflies.ai/), [Fathom](https://fathom.video/) ou [MeetGeek](https://meetgeek.ai/)

## 1. Dictée open source : parler et écrire dans l’application active

### Multiplateforme

- [Handy — GitHub](https://github.com/cjpais/Handy) — Linux, macOS, Windows ; local/hors ligne ; colle le texte dans le champ actif.
- [OpenWhispr — GitHub](https://github.com/OpenWhispr/openwhispr) — Linux, macOS, Windows ; moteurs locaux ou cloud avec sa propre clé.
- [Whispering / Epicenter — GitHub](https://github.com/EpicenterHQ/epicenter/tree/main/apps/whispering) — Linux, macOS, Windows et web ; local et fournisseurs cloud.
- [Amical — GitHub](https://github.com/amicalhq/amical) · [site](https://amical.ai/) — macOS et Windows ; local-first, dictée contextuelle.
- [whisper-writer — GitHub](https://github.com/savbell/whisper-writer) — Linux, macOS, Windows ; Faster-Whisper local ou API OpenAI ; raccourci global.
- [Voquill — GitHub](https://github.com/voquill/voquill) — Linux, macOS, Windows ; Whisper local ou cloud, glossaire et nettoyage du texte.
- [VoiceTypr — GitHub](https://github.com/moinulmoin/voicetypr) — macOS et Windows ; moteur local ; code ouvert, binaires commerciaux.
- [Tambourine Voice — GitHub](https://github.com/kstonekuan/tambourine-voice) — macOS et Windows ; moteurs STT/LLM configurables.
- [HNS — GitHub](https://github.com/primaprashant/hns) — Linux, macOS, Windows ; outil CLI local, micro vers presse-papiers.
- [Scribe — GitHub](https://github.com/perrette/scribe) — Linux, macOS et Windows ; CLI et icône de barre système, saisie dans la fenêtre active, backends locaux (Whisper, FUTO, Vosk) ou cloud (Groq, OpenAI).

### macOS

- [VoiceInk — GitHub](https://github.com/Beingpax/VoiceInk) — dictée native, moteurs locaux et option BYOK.
- [FluidVoice — GitHub](https://github.com/altic-dev/FluidVoice) — Parakeet, Apple Speech et Whisper ; saisie dans toute application.
- [OpenSuperWhisper — GitHub](https://github.com/Starmel/OpenSuperWhisper) — application Swift native, Whisper/Parakeet local.
- [Pindrop — GitHub](https://github.com/watzon/pindrop) — barre de menus, WhisperKit local, nettoyage IA optionnel.
- [FnKey — GitHub](https://github.com/evoleinik/fnkey) — maintenir Fn, parler, coller ; Deepgram/Groq.
- [Ghost Pepper — GitHub](https://github.com/matthartman/ghost-pepper) — Apple Silicon ; modèles vocaux locaux, dictée et réunions.
- [TypeWhisper — GitHub](https://github.com/TypeWhisper/typewhisper-mac) — dictée locale avec cloud optionnel.
- [Ito AI — GitHub](https://github.com/ito-ai/ito) — dictée vocale open source pour Mac.

### Windows

- [OmniDictate — GitHub](https://github.com/gurjar1/OmniDictate) — dictée temps réel locale dans toute application.
- [Chirp — GitHub](https://github.com/Whamp/chirp-stt) — Parakeet local sur CPU, conçu pour Windows.
- [Whisper Desktop — GitHub](https://github.com/Const-me/Whisper) — interface Windows locale basée sur whisper.cpp.
- [whisper-standalone-win — GitHub](https://github.com/Purfview/whisper-standalone-win) — exécutables Windows autonomes pour Whisper/Faster-Whisper.

### Linux

- [nerd-dictation — GitHub](https://github.com/ideasman42/nerd-dictation) — dictée hors ligne légère avec Vosk.
- [Elograf — GitHub](https://github.com/papoteur-mga/elograf) — interface graphique pour nerd-dictation.
- [hyprwhspr — GitHub](https://github.com/goodroot/hyprwhspr) — dictée Linux native ; Whisper.cpp, Parakeet ou cloud BYOK.
- [Dabri — GitHub](https://github.com/AshBuk/dabri) — dictée Linux native, locale et centrée confidentialité.
- [Vocalinux — GitHub](https://github.com/jatinkrmalik/vocalinux) — Whisper.cpp, Whisper ou Vosk ; X11 et Wayland.
- [VOXD — GitHub](https://github.com/jakovius/voxd) — interface graphique, barre système et CLI ; Whisper.cpp local.
- [VoxType — GitHub](https://github.com/peteonrails/voxtype) — push-to-talk pour Wayland, plusieurs moteurs locaux.
- [whisper_dictation — GitHub](https://github.com/themanyone/whisper_dictation) — clavier vocal Linux, commandes vocales et fonctions multimodales.

### Android et iOS

- [Whisper IME — GitHub](https://github.com/woheller69/whisperIME) — clavier Android Whisper hors ligne ; également distribué via F-Droid.
- [Transcribro — GitHub](https://github.com/soupslurpr/Transcribro) — clavier/service Android local et privé.
- [Offline Voice Input — GitHub](https://github.com/notune/android_transcribe_app) — clavier Android hors ligne et sous-titres en direct.
- [WhisperBoard — GitHub](https://github.com/Saik0s/Whisperboard) — enregistrement et transcription locale sur iOS.

## 2. Applications open source pour fichiers audio/vidéo, sous-titres et réunions

- [Buzz — GitHub](https://github.com/chidiwilliams/buzz) — bureau Linux/macOS/Windows ; micro ou fichiers ; hors ligne.
- [Vibe — GitHub](https://github.com/thewh1teagle/vibe) — bureau Linux/macOS/Windows ; audio/vidéo local avec Whisper.cpp.
- [Whishper — GitHub](https://github.com/pluja/whishper) — interface web auto-hébergeable, transcription, traduction et édition de sous-titres.
- [Scriberr — GitHub](https://github.com/rishikanthc/Scriberr) — transcription locale, diarisation et résumés optionnels.
- [Meetily — GitHub](https://github.com/Zackriya-Solutions/meeting-minutes) — assistant de réunion local/auto-hébergeable, macOS et Windows.
- [Whisper WebUI — GitHub](https://github.com/jhj0517/Whisper-WebUI) — interface web pour Whisper, Faster-Whisper et sous-titres.
- [Whisper-WebUI — GitHub](https://github.com/numz/whisper-stt) — interface web locale de transcription.
- [Whisper-Web — GitHub](https://github.com/xenova/whisper-web) — transcription dans le navigateur avec Transformers.js/WebGPU.
- [WhisperLive — GitHub](https://github.com/collabora/WhisperLive) — transcription temps réel auto-hébergeable.
- [WhisperX — GitHub](https://github.com/m-bain/whisperX) — timestamps par mot, alignement et diarisation.
- [Stable-ts — GitHub](https://github.com/jianfch/stable-ts) — timestamps et sous-titres plus précis avec Whisper.
- [Subtitle Edit — GitHub](https://github.com/SubtitleEdit/subtitleedit) — éditeur de sous-titres avec moteurs speech-to-text.
- [Aiko — site](https://sindresorhus.com/aiko) — transcription locale sur macOS/iOS.
- [MacWhisper — site](https://goodsnooze.gumroad.com/l/macwhisper) — transcription de fichiers sur macOS, freemium.
- [Whisper Memos — site](https://whispermemos.com/) — application iOS de mémos vocaux transcrits.
- [Speech Note — GitHub](https://github.com/mkiol/dsnote) — dictée et transcription locale pour Linux.
- [Screenpipe — GitHub](https://github.com/mediar-ai/screenpipe) — capture locale continue de l’écran et de l’audio avec recherche.
- [writeout.ai — GitHub](https://github.com/beyondcode/writeout.ai) — application Laravel auto-hébergeable pour transcrire et traduire.
- [WaaS — GitHub](https://github.com/schibsted/WAAS) — interface/API auto-hébergeable autour de Whisper.

## 3. Applications et services commerciaux de dictée

- [Wispr Flow](https://wisprflow.ai/) — dictée dans toutes les applications ; Mac, Windows, iPhone et Android.
- [Superwhisper](https://superwhisper.com/) — dictée et transcription, surtout macOS/iOS ; modes locaux selon configuration.
- [Aqua Voice](https://withaqua.com/) — dictée et reformulation pour Mac/Windows.
- [Willow Voice](https://willowvoice.com/) — dictée IA contextuelle.
- [Typeless](https://www.typeless.com/) — dictée IA multiplateforme.
- [Dragon Professional](https://www.nuance.com/dragon/business-solutions/dragon-professional.html) — dictée professionnelle Windows et commandes vocales.
- [Dragon Anywhere](https://www.nuance.com/dragon/dragon-anywhere.html) — dictée mobile iOS/Android dans l’application Dragon.
- [Braina](https://www.brainasoft.com/braina/) — assistant Windows avec dictée multilingue.
- [Speechnotes](https://speechnotes.co/) — bloc-notes et dictée web/mobile.
- [SpeechTexter](https://www.speechtexter.com/) — dictée web multilingue.

### Fonctions intégrées gratuites ou natives

- [Dictée Apple](https://support.apple.com/guide/mac-help/use-dictation-mh40584/mac) — intégrée à macOS ; également disponible sur iPhone/iPad.
- [Saisie vocale Windows](https://support.microsoft.com/windows/use-voice-typing-to-talk-instead-of-type-on-your-pc-fec94565-c4bd-329d-e59a-af033fa5689f) — raccourci `Win + H`.
- [Google Docs — saisie vocale](https://support.google.com/docs/answer/4492226) — dictée dans Google Docs via navigateur compatible.
- [Microsoft Word — Dictée](https://support.microsoft.com/office/dictate-your-documents-in-word-eab203e1-d030-43c1-84ef-999b0b9675fe) — fonction Microsoft 365.
- [Gboard](https://support.google.com/gboard/answer/2781851) — saisie vocale du clavier Google sur mobile.
- [Google Recorder](https://recorder.google.com/) — enregistrement/transcription sur appareils Pixel et accès web aux enregistrements synchronisés.
- [Live Transcribe](https://www.android.com/accessibility/live-transcribe/) — transcription en direct Android orientée accessibilité.

## 4. Transcription web, interviews, podcasts et création de contenu

- [Descript](https://www.descript.com/) — transcription et montage audio/vidéo par le texte.
- [Notta](https://www.notta.ai/) — enregistrement, import de fichiers, réunions et transcription multilingue.
- [Sonix](https://sonix.ai/) — transcription, sous-titres, traduction et collaboration.
- [Trint](https://trint.com/) — transcription et édition collaborative, médias/entreprises.
- [Happy Scribe](https://www.happyscribe.com/) — transcription automatique ou humaine, sous-titres et traduction.
- [Rev](https://www.rev.com/) — transcription IA ou humaine, sous-titres et légendes.
- [Temi](https://www.temi.com/) — transcription automatique simple de fichiers.
- [TurboScribe](https://turboscribe.ai/) — transcription de fichiers par lot.
- [Transkriptor](https://transkriptor.com/) — audio/vidéo, réunions et résumés.
- [Amberscript](https://www.amberscript.com/) — transcription et sous-titrage automatique/humain.
- [Cockatoo](https://www.cockatoo.com/) — transcription web de fichiers audio/vidéo.
- [Riverside Transcription](https://riverside.fm/transcription) — transcription liée à l’enregistrement de podcasts/vidéos.
- [VEED](https://www.veed.io/tools/transcription) — transcription et sous-titres dans un éditeur vidéo web.
- [Kapwing](https://www.kapwing.com/tools/transcription) — transcription et sous-titres vidéo en ligne.
- [Adobe Premiere Pro — Speech to Text](https://helpx.adobe.com/premiere-pro/using/speech-to-text.html) — transcription et sous-titrage dans Premiere.

## 5. Réunions, visioconférences et prise de notes automatique

- [Otter.ai](https://otter.ai/) — transcription temps réel, résumés, recherche et intégrations de réunion.
- [Fireflies.ai](https://fireflies.ai/) — bot de réunion, transcription, résumés et intégrations CRM.
- [Fathom](https://fathom.video/) — enregistrement, transcription et résumés de visioconférences.
- [tl;dv](https://tldv.io/) — Zoom/Google Meet/Teams, transcription, clips et résumés.
- [MeetGeek](https://meetgeek.ai/) — réunions planifiées, transcription, notes et actions.
- [Read AI](https://www.read.ai/) — transcription et analyses de réunions.
- [Krisp AI Meeting Assistant](https://krisp.ai/ai-meeting-assistant/) — transcription/résumé avec réduction de bruit.
- [Grain](https://grain.com/) — réunions, transcription et extraits vidéo partageables.
- [Avoma](https://www.avoma.com/) — assistant de réunion et intelligence conversationnelle/CRM.
- [Sembly AI](https://www.sembly.ai/) — notes, transcription et tâches issues des réunions.
- [Jamie](https://www.meetjamie.ai/) — notes de réunion sans bot visible dans l’appel.
- [Granola](https://www.granola.ai/) — notes et transcription de réunions sur ordinateur.
- [Zoom AI Companion](https://www.zoom.com/en/products/ai-assistant/) — transcription et résumés dans Zoom.
- [Microsoft Teams transcription](https://support.microsoft.com/office/view-live-transcription-in-microsoft-teams-meetings-7a1401f4-470d-418c-b404-6ca8c5eab1f5) — transcription en direct dans Teams.
- [Google Meet transcription](https://support.google.com/meet/answer/12849897) — transcription native selon l’offre Google Workspace.

## 6. Moteurs, bibliothèques et API pour construire sa propre application

### Open source / exécution locale

- [OpenAI Whisper — GitHub](https://github.com/openai/whisper) — modèle ASR multilingue de référence.
- [whisper.cpp — GitHub](https://github.com/ggml-org/whisper.cpp) — implémentation C/C++ locale, Apple Silicon/CUDA/Vulkan/WASM.
- [Faster-Whisper — GitHub](https://github.com/SYSTRAN/faster-whisper) — implémentation CTranslate2 rapide et économe en mémoire.
- [Vosk — GitHub](https://github.com/alphacep/vosk-api) — reconnaissance vocale hors ligne légère, nombreuses plateformes.
- [Kaldi — GitHub](https://github.com/kaldi-asr/kaldi) — boîte à outils ASR classique et très complète.
- [NVIDIA NeMo — GitHub](https://github.com/NVIDIA-NeMo/NeMo) — framework incluant des modèles ASR comme Parakeet.
- [SpeechBrain — GitHub](https://github.com/speechbrain/speechbrain) — toolkit PyTorch pour parole et audio.
- [ESPnet — GitHub](https://github.com/espnet/espnet) — toolkit end-to-end pour reconnaissance et synthèse vocale.
- [sherpa-onnx — GitHub](https://github.com/k2-fsa/sherpa-onnx) — ASR local/streaming pour mobile, bureau, web et embarqué.
- [WhisperKit — GitHub](https://github.com/argmaxinc/WhisperKit) — Whisper optimisé pour l’écosystème Apple.
- [Moonshine — GitHub](https://github.com/usefulsensors/moonshine) — modèles ASR rapides pour appareils limités.
- [RealtimeSTT — GitHub](https://github.com/KoljaB/RealtimeSTT) — bibliothèque Python temps réel avec VAD, wake words, flux audio et plusieurs moteurs ; ce n’est pas une application prête à l’emploi.
- [Kroko ONNX — GitHub](https://github.com/kroko-ai/kroko-onnx) — moteur ASR local et streaming utilisé notamment par RealtimeSTT ; vérifier séparément les licences des modèles.
- [SenseVoice — GitHub](https://github.com/FunAudioLLM/SenseVoice) — ASR pour mandarin, cantonais, anglais, japonais et coréen, avec détection de langue, émotion et événements audio.
- [Mozilla DeepSpeech — GitHub](https://github.com/mozilla/DeepSpeech) — moteur TensorFlow historique pour reconnaissance hors ligne/embarquée ; projet archivé, à considérer surtout pour maintenance ou recherche.
- [Coqui STT — GitHub](https://github.com/coqui-ai/STT) — continuation historique de DeepSpeech avec inférence streaming ; le dépôt indique qu’il n’est plus activement maintenu.
- [SpeechRecognition — GitHub](https://github.com/Uberi/speech_recognition) — interface Python vers plusieurs moteurs et API de reconnaissance, en ligne ou hors ligne.
- [pyannote.audio — GitHub](https://github.com/pyannote/pyannote-audio) — briques de diarisation et détection de locuteurs ; complète un moteur STT mais ne le remplace pas.
- [pydub — GitHub](https://github.com/jiaaro/pydub) — manipulation et prétraitement audio en Python ; outil auxiliaire, pas un moteur STT.
- [NVIDIA Parakeet TDT 0.6B v3 — Hugging Face](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) — modèle ASR multilingue de NVIDIA, utilisable notamment via NeMo ; vérifier la licence du modèle et la compatibilité matérielle.
- [Qwen3-ASR 1.7B — Hugging Face](https://huggingface.co/Qwen/Qwen3-ASR-1.7B) — modèle de reconnaissance vocale de la famille Qwen, destiné à la transcription multilingue.
- [Voxtral Mini 3B — Hugging Face](https://huggingface.co/mistralai/Voxtral-Mini-3B-2507) — modèle audio/texte de Mistral AI capable notamment de transcription et de compréhension audio.
- [PocketSphinx — GitHub](https://github.com/cmusphinx/pocketsphinx) — petit moteur de reconnaissance vocale de la famille CMU Sphinx, adapté aux usages légers et au vocabulaire contraint.
- [Julius — GitHub](https://github.com/julius-speech/julius) — moteur historique de reconnaissance continue à grand vocabulaire ; surtout pertinent pour systèmes classiques et recherche.
- [Flashlight — GitHub](https://github.com/flashlight/flashlight) — bibliothèque C++ de machine learning ayant servi à des pipelines de reconnaissance vocale ; ce n’est pas une application STT prête à l’emploi.

### API cloud

- [OpenAI Audio API](https://platform.openai.com/docs/guides/speech-to-text) — transcription et traduction audio via API.
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text) — streaming/batch et adaptation.
- [Microsoft Azure Speech to Text](https://azure.microsoft.com/products/ai-services/speech-to-text) — temps réel, batch et modèles personnalisés.
- [Amazon Transcribe](https://aws.amazon.com/transcribe/) — streaming/batch, vocabulaire et identification de canaux/intervenants.
- [Deepgram](https://deepgram.com/) — API temps réel et fichiers, modèles vocaux spécialisés.
- [AssemblyAI](https://www.assemblyai.com/) — API transcription avec diarisation et fonctions d’intelligence audio.
- [Speechmatics](https://www.speechmatics.com/) — API temps réel/batch, multilingue et déploiements entreprise.
- [Gladia](https://www.gladia.io/) — API transcription temps réel et asynchrone.
- [ElevenLabs Speech to Text](https://elevenlabs.io/speech-to-text) — API de transcription et diarisation.
- [Groq Speech-to-Text](https://console.groq.com/docs/speech-to-text) — inférence rapide de modèles Whisper via API.
- [Replicate Whisper](https://replicate.com/openai/whisper) — Whisper hébergé à la demande.

## 7. Projets GitLab

> Les pages GitLab sont parfois peu descriptives sans connexion. Les liens ci-dessous ont été conservés comme projets ou index pertinents, sans leur attribuer de compteur d’étoiles figé.

- [AA Speech To Text — GitLab](https://gitlab.com/ron.gr/aa-speech-to-text) — projet Android visant la reconnaissance vocale pour des langues non prises en charge nativement dans certains usages Android Auto.
- [VRChat Speech Assistant — GitLab](https://gitlab.com/ameliend/vrchat-speech-assistant) — assistant speech-to-text/traduction destiné à VRChat sous Windows.
- [Capacitor Speech Recognition — GitLab](https://gitlab.com/mobicoop/capacitor-speech-recognition) — fork d’un plugin Capacitor de reconnaissance vocale pour applications mobiles.
- [Speech-to-Text Recognition and Transcription Criticism — GitLab](https://gitlab.com/uniluxembourg/c2dh/u-core/speech-to-text-recognition-and-transcription-criticism) — ressource/projet universitaire du C2DH, Université du Luxembourg.
- [Topic GitLab “transcription”](https://gitlab.com/explore/projects/topics/transcription) — index de projets GitLab liés à la transcription.
- [Topic GitLab “STT”](https://gitlab.com/explore/projects/topics/stt) — index de projets GitLab portant le tag STT.

## 8. Outils complémentaires et datasets

### Intégrations spécialisées

- [Kdenlive](https://kdenlive.org/) — l’éditeur vidéo intègre des fonctions speech-to-text pour créer et éditer des sous-titres ; vérifier la documentation de la version installée pour les moteurs disponibles.

### Jeux de données

- [Mozilla Common Voice](https://commonvoice.mozilla.org/) — corpus vocal multilingue ouvert pour entraîner et évaluer des systèmes de parole.
- [LibriSpeech](https://www.openslr.org/12/) — corpus anglais d’environ 1 000 heures de livres audio lus.

### Modèles préentraînés

- [Modèles Whisper](https://github.com/openai/whisper#available-models-and-languages) — tailles, besoins mémoire, langues et compromis vitesse/précision.
- [Modèles Vosk](https://alphacephei.com/vosk/models) — modèles téléchargeables par langue et par taille.

### Repères par fonctionnalité

| Besoin | Options à examiner |
|---|---|
| Application desktop simple, locale | Handy, OpenWhispr, OmniDictate, VoiceInk |
| Transcription de fichiers hors ligne | Buzz, Vibe, Whishper |
| Développement temps réel | RealtimeSTT, sherpa-onnx, WhisperLive, Kroko ONNX |
| Appareil limité ou embarqué | whisper.cpp, Vosk, sherpa-onnx |
| Diarisation des intervenants | WhisperX, pyannote.audio |
| ASR multilingue généraliste | Whisper, Faster-Whisper, whisper.cpp |
| Chinois, japonais ou coréen | SenseVoice, Whisper |

## 9. Répertoires et pages de découverte à surveiller

- [Awesome Voice Typing — GitHub](https://github.com/primaprashant/awesome-voice-typing) — liste spécialisée dans la dictée open source.
- [Awesome Whisper — GitHub](https://github.com/sindresorhus/awesome-whisper) — applications, interfaces web, CLI et API autour de Whisper.
- [Awesome Whisper Apps — GitHub](https://github.com/danielrosehill/Awesome-Whisper-Apps) — collection complémentaire d’applications et d’outils utilisant Whisper, classés par plateforme et usage.
- [Topic GitHub “speech-to-text”](https://github.com/topics/speech-to-text) — projets classés par activité/popularité.
- [Topic GitHub “transcription”](https://github.com/topics/transcription) — projets de transcription et sous-titrage.
- [Topic GitHub “speech-recognition”](https://github.com/topics/speech-recognition) — moteurs, bibliothèques et applications de reconnaissance vocale.
- [Recherche GitLab “speech-to-text”](https://gitlab.com/explore/projects?name=speech-to-text) — projets publics correspondants sur GitLab.
- [Recherche Codeberg “Whisper”](https://codeberg.org/explore/repos?q=whisper&topic=false) — dépôts publics sur Codeberg.
- [F-Droid — recherche speech-to-text](https://search.f-droid.org/?q=speech+to+text) — applications Android libres.

## Conseils de sélection

1. **Données sensibles :** privilégier un outil explicitement local/hors ligne ; “IA” ou “application de bureau” ne veut pas forcément dire traitement local.
2. **Dictée ou transcription :** pour écrire dans n’importe quelle application, choisir une vraie application de dictée avec raccourci global ; pour podcasts/réunions, choisir une application avec diarisation, timestamps et export.
3. **Français :** vérifier le français, la ponctuation, les noms propres et les accents avec un échantillon réel avant achat.
4. **Réunions :** informer les participants et respecter les lois/règles locales sur l’enregistrement et le consentement.
5. **Open source :** vérifier la licence, la date de la dernière version, les issues récentes et l’existence de binaires signés ; un dépôt public n’est pas toujours facile à installer.

## Sources de départ de la recherche

- [Awesome Voice Typing](https://github.com/primaprashant/awesome-voice-typing)
- [Awesome Whisper](https://github.com/sindresorhus/awesome-whisper)
- [GitHub Topics — speech-to-text](https://github.com/topics/speech-to-text)
- [GitHub Topics — transcription](https://github.com/topics/transcription)
- [TechRadar — Speech-to-text apps](https://www.techradar.com/news/best-speech-to-text-app)
- [Zapier — AI meeting assistants](https://zapier.com/blog/best-ai-meeting-assistant/)
