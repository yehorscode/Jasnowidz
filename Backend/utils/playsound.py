import playsound

def play(file_path):
    playsound.playsound(file_path)

def finish():
    play("finish.mp3")