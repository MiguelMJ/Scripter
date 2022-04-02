<h1 align="center">Scripter</h1>

<h3 align="center">Create interactive scripts from recordings for language learning</h3>

<p align="center">
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/-Python_3-black?style=for-the-badge&logo=python"></a>
    <a href="https://deepgram.com"><img src="https://img.shields.io/badge/-Deepgram-black?style=for-the-badge"></a>
    <a href="https://github.com/LibreTranslate/LibreTranslate"><img src="https://img.shields.io/badge/-LibreTranslate-black?style=for-the-badge"></a>
    <a href="LICENSE"><img " src="https://img.shields.io/badge/License-MIT-black?style=for-the-badge"></a>
</p>

Create interactive HTML5 pages with a script from a recorded conversation. Powered by Deepgram. Requires API key from Deepgram. Submission for Deepgram+DEV hackathon, 2022.

## Get the API key
- Deepgram (required): Create an account in deepgram.com and get an API key.

Store it in a file named `deepgramApiKey` in the root folder or pass it directly in the CLI using the `--deepgram-api-key` argument.

## Features
- **Tune the voice recognition process** with the Deepgram [query parameters for transcriptions pre-recorded audio](https://developers.deepgram.com/api-reference/#transcription-prerecorded) with `-P|--param KEY=VALUE` arguments.
- Downloads and results are **cached to reduce redundant traffic**, but you can force it using the `-F|--force` flag or directly removing the `_cache` folder.
- All log information outputs through stderr and the search output through stdout (or a file, with the `-o|--output-file FILE` argument). This makes it easy to redirect and **pipe different information safely**.
- Use the `-H|--host HOST` option to **set the LibreTranslate host to call** for translations. By default, https://libretranslate.de is called, but a local server is recommended.
- Your language of use must be supported by both Deepgram and LibreTranslate. Set the **source and target languages** respectively with `-f|--from LANG` and `-t|--to LANG`.
     
## Quick start
- Install all dependencies:
    ```bash
    pip install -r requirements.txt
    ```
- Generate an interactive script from a conversation in Spanish, using English translations.
    ```bash
    python main.py --from es --to en example_audio.ogg -o index.html
    ```

### Set up a local LibreTranslate server (optional)
```bash
# Install the application
pip install libretranslate

# Launch it
# IMPORTANT: use --load-only to avoid loading
# the innecesary models of all supported languages
libretranslate --load-only es,en --disable-web-ui
```
Now you can use Scripter with the `--host http://localhost:5000` argument.

## Contributing
- See the [CONTRIBUTING](CONTRIBUTING.md) file to make a PR.
- :star: Star this repository [![](https://img.shields.io/github/stars/MiguelMJ/AudioSearchEngine?style=social)](https://github.com/MiguelMJ/AudioSearchEngine/stargazers)
- Raise an issue  [![](https://img.shields.io/github/issues/MiguelMJ/AudioSearchEngine?style=social&logo=github)](https://github.com/MiguelMJ/AudioSearchEngine/issues).

## Contributors
Empty section, for now ;)

## Ideas for the future

- Allow usage of output templates.
- Enable options to change which APIs to use for the transcription and translation services.
- Add a demo.
        
## License
This code is licensed under the MIT license, a copy of which is available in the repository.
