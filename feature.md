# Feature

基于[IndexTTS HTTP Service](./api/indextts2.yml)所提供的底层能力，本项目希望在此基础上提供更加完善的服务。包括且不限于：

- 异步文生语音服务：用户输入一段文字，我们返回对应的音频文件。用户可以指定对应的音色和声音情感来生成音频，具体能力来自于[IndexTTS HTTP Service](./api/indextts2.yml)服务。可以参考Minimaxi的Text to Speech功能：https://www.minimax.io/platform/document/T2A%20V2?key=66719005a427f0c8a5701643

- 声音文件上传：用户可以上传一份音频文件，我们保存这个文件，用于后续的音色克隆。可以参考Minimaxi的Voice Cloning中的File Upload功能：https://www.minimax.io/platform/document/Voice%20Cloning?key=66719032a427f0c8a570165b

- 音色克隆功能：用户可以指定某个已经上传的音频文件，使用这个音频文件中的音色作为文字转语音的音色。可以参考Minimaxi的Voice Cloning功能：https://www.minimax.io/platform/document/Voice%20Cloning?key=66719032a427f0c8a570165b

- 音色删除功能：用户可以删除某个指定的音色和其对应的声音文件。

- 音色获取功能：用户可以获取某个指定的克隆的音色的试听效果音频。

- 音色列举功能：用户可以列举他所有的已经克隆的音色。

- 队列管理功能：由于[IndexTTS HTTP Service](./api/indextts2.yml)是串行处理的，处理能力有限，同一时间只支持一个任务的处理，因此我们要集成队列管理功能。
