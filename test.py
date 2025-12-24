from model import extract_event, format_event_for_display, process_text

if __name__ == "__main__":
    text = "Созвон с командой завтра в 15:00 в Zoom"
    
    print(f"Входной текст: {text}\n")

    event = process_text(text)
    print(event.to_json()) # тут полный json с кучей доп данных по типу какой скор у сущности и тд.
    print('-----------------')
    result = extract_event(text) # тут только основные нужные данные по событию.
    print(result)
    print('-----------------')
    print("\n" + format_event_for_display(result)) # тут красивый человекочитаемый формат
