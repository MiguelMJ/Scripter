import argparse
import json
import os
import re
import requests
import sys

#
# Output functions
#
log_level = 2
red = "\033[38;5;9m"
green = "\033[38;5;10m"
yellow = "\033[38;5;11m"
bold = "\033[1m"
reset = "\033[0m"


def no_color():
    global red
    global green
    global yellow
    global bold
    global reset
    red = ""
    green = ""
    yellow = ""
    bold = ""
    reset = ""


def log_info(msg, **kargs):
    if log_level >= 2:
        print(msg, file=sys.stderr, **kargs)
        sys.stderr.flush()


def log_important(msg, **kargs):
    if log_level >= 2:
        print(f"{bold}> {msg}{reset}", file=sys.stderr, **kargs)
        sys.stderr.flush()


def log_success(msg, **kargs):
    if log_level >= 2:
        print(f"{green}\u2714 {msg}{reset}", file=sys.stderr, **kargs)
        sys.stderr.flush()


def log_warning(msg, **kargs):
    if log_level >= 1:
        print(f"{yellow}\u26A0 {msg}{reset}", file=sys.stderr, **kargs)
        sys.stderr.flush()


def log_error(msg, **kargs):
    if log_level >= 0:
        print(f"{red}\u2716 {msg}{reset}", file=sys.stderr, **kargs)
        sys.stderr.flush()


def set_log_level(level):
    global log_level
    if level < -1 or level > 2:
        raise "Invalid log level"
    log_level = level


def abort(code, msg, **kargs):
    log_error(msg, **kargs)
    exit(code)


#
# Cache management
#

## Get the path to a cached response associated to an input file
def get_cache_path(infile):
    ofile = re.sub(r"^\.+", "", infile.replace("/", "_"))
    return f"{cache_dir}/{ofile}"


## Call Deepgram API to get the transcription of an audio
def get_transcription(audio_file, api_token, url_params, **kargs):
    cache_file = get_cache_path(audio_file + ".json")
    log_important(f"Getting transcription [{audio_file}]")
    if kargs.get("ignore_cache"):
        log_info("Ignore cache")
    elif os.path.exists(cache_file):
        log_info("Cache hit")
        with open(cache_file) as f:
            obj = json.load(f)
        transcript = obj["results"]["channels"][0]["alternatives"][0]["transcript"]
        if len(transcript) == 0:
            log_warning(f"Empty transcription")
        else:
            log_success("Transcription returned successfully")
        return obj
    else:
        log_info("Cache fail")
    url_params_str = "&".join(f"{k}={url_params[k]}" for k in url_params)
    url = f"https://api.deepgram.com/v1/listen?{url_params_str}"
    headers = {"Authorization": f"Token {api_token}"}
    with open(audio_file, "rb") as fh:
        response = requests.post(url, headers=headers, data=fh)
        obj = json.loads(response.text)
        obj["source_file"] = audio_file
        if response:
            transcript = obj["results"]["channels"][0]["alternatives"][0]["transcript"]
            if len(transcript) == 0:
                log_warning(f"Empty transcription")
            else:
                log_success("Transcription returned successfully")
            log_info("Saving in cache...")
            with open(cache_file, "w") as f:
                json.dump(obj, f)
            return obj
        else:

            abort(
                response.status_code,
                f"Status {response.status_code}: {obj['error']} - {obj['reason']}",
            )


## Call LibreTranslate API to get a translation
def get_translation(server, source, target, txt):
    log_important(f"Translating from {source} to {target}")
    response = requests.post(
        f"{server}/translate",
        data=json.dumps({"q": txt, "source": source, "target": target}),
        headers={"Content-Type": "application/json"},
    )
    log_info(txt)
    translation = json.loads(response.text)
    if "error" in translation:
        log_info(translation["error"])
        log_error("Translation failed")
        return translation["error"]
    log_info(translation["translatedText"])
    log_success("Translation successful")
    return translation["translatedText"]


## Function to assure that a file is read
def read_file(path):
    try:
        with open(path) as f:
            text = f.read()
        log_info(f"Successfully read {path}")
        return text.strip()
    except IOError as e:
        abort(-1, f"Error encountered reading {path}: {e.what()}")


def tag(name, content, attributes=dict()):
    attrstr = ""
    for k in attributes:
        attrstr += f' {k}="{attributes[k]}"'
    return f"<{name}{attrstr}> {content} </{name}>"


def elaborate_script(file, transcription, args):
    log_important("Generating HTML from transcript")
    html = f"""
    <audio id="dialog" controls><source src="{file}" type="audio/{file.split(".")[-1]}">Audio not supported by your browser</audio>

    <style>
    audio {{ margin: 1cm }}
        
    .speaker0 {{ color: red }}
    .speaker1 {{ color: blue }}
    .speaker2 {{ color: green }}
    .speaker3 {{ color: orange }}
    .speaker4 {{ color: magenta }}
    .speaker5 {{ color: cyan }}
    
    #transcript {{ margin-left: 0.3cm }}
    #transcript li {{ margin-bottom: 0.3cm }}
    #transcript li:hover {{ cursor: pointer; text-decoration: underline }}

    footer {{ position: fixed; left:0.3cm; bottom:0.3cm }}
    </style>
    
    <script>
    audio = document.getElementById("dialog")
    playedfromsentence = false
    function play(start, end){{
        if(playedfromsentence) return
        let audiomargin = 0.2
        audio.currentTime = start-audiomargin
        audio.play()
        playedfromsentence = true
        let ms = Math.floor((end-start+2*audiomargin)*1000)
        setTimeout(()=>{{
            audio.pause()
            playedfromsentence = false
        }}, ms)
    }}
    </script>
    <hr>
    """
    html = re.sub("\n    ", "\n", html)
    words = transcription["results"]["channels"][0]["alternatives"][0]["words"]
    prev_speaker = -1
    phrase_id = 1
    last_phrase_content = ""
    phrase_start = 0
    phrase_end = 0
    script = ""
    for word in words:
        if prev_speaker != word["speaker"]:
            if prev_speaker > -1:  # speaker changed (or start of conversation)
                attrs = {
                    "class": "speaker" + str(prev_speaker),
                    "onClick": f"play({phrase_start},{phrase_end})",
                    "title": get_translation(
                        args.host,
                        args.from_,
                        args.to,
                        last_phrase_content,
                    ),
                }
                script += tag("li", last_phrase_content, attrs) + "\n"
                last_phrase_content = ""
                phrase_start = word["start"]
            prev_speaker = word["speaker"]
        last_phrase_content += word["punctuated_word"] + " "
        phrase_end = word["end"]

    html += tag("ol", script, {"id": "transcript"})
    log_success("HTML ready")
    html += """<footer>Interactive script generated by <a href="https://github.com/MiguelMJ/Scripter">Scripter</a>, powered by Deepgram and LibreTranslate.</footer>"""
    return html


## Function to assure that a folder exists
def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def parse_arguments():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTIONS] FILE",
        description=f"Elaborate interactive scripts from conversation audios. Powered by Deepgram and LibreTranslate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Source code: https://github.com/MiguelMJ/Scripter",
    )
    parser.add_argument("file", help="Audio file with the conversation", metavar="FILE")
    parser.add_argument(
        "--no-ansi", help="Don't display color in the output", action="store_true"
    )
    parser.add_argument(
        "-L",
        "--log-level",
        help="log level. -1=quiet, 0=errors, 1=warnings, 2=info (default=2)",
        type=int,
        default=2,
        metavar="NUM",
    )
    parser.add_argument(
        "-f",
        "--from",
        help="source language (default=es)",
        default="es",
        dest="from_",
        metavar="X",
    )
    parser.add_argument(
        "-t",
        "--to",
        help="target language (default=en)",
        default="en",
        metavar="X",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        help="file to store the results of the search in a JSON format",
        metavar="FILE",
    )
    group = parser.add_argument_group("Deepgram options")
    group.add_argument(
        "--deepgram-api-key",
        help="Deepgram API key. By default, get it from a file named deepgramApiKey",
        metavar="X",
    )
    group.add_argument(
        "-P",
        "--param",
        help="parameter for the Deepgram URL",
        action="append",
        metavar="X=Y",
    )
    group.add_argument(
        "-F",
        "--ignore-cache",
        help="ignore cached transcriptions and force an API call",
        action="store_true",
    )
    group = parser.add_argument_group("LibreTranslate options")
    group.add_argument(
        "-H",
        "--host",
        help="host to which perform the translation requests (default=https://libretranslate.de)",
        default="https://libretranslate.de",
        metavar="X",
    )
    return parser.parse_args()


#
# Main
#
if __name__ == "__main__":
    # Initialize folders
    cache_dir = "./_cache"
    create_folder(cache_dir)

    # Parse CLI args
    args = parse_arguments()
    if args.no_ansi:
        no_color()
    set_log_level(args.log_level)
    # Deepgram related info
    deepgram_api_key = args.deepgram_api_key or read_file("deepgramApiKey")
    deepgram_params = {
        "language": args.from_,
        "model": "general",
        "punctuate": "true",
        "diarize": "true",
        "utterances": "false",
        "alternatives": "1",
    }
    if args.param:
        for param in args.param:
            [k, v] = param.split("=")
            if k == "diarize" and v.lower() != "true":
                abort(-1, "The script requires the diarize flag on")
            if k == "punctuate" and v.lower() != "true":
                abort(-1, "The script requires the punctuate flag on")
            deepgram_params[k] = v
    log_info(
        "Deepgram URL params:\n"
        + "\n".join(f"{k:15}{deepgram_params[k]}" for k in deepgram_params)
    )
    log_info("LibreTranslate host: "+args.host)
    audio = args.file

    # Get transcription
    transcription = get_transcription(
        audio, deepgram_api_key, deepgram_params, ignore_cache=args.ignore_cache
    )
    # Do the search
    script = elaborate_script(audio, transcription, args)
    if args.output_file:
        with open(args.output_file, "w") as out:
            out.write(script)
    else:
        print(script)
