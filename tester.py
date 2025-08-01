numbers = [1, 3, 2, 4, 5, 3, 2, 4, 1]
_dict: dict[int, int] = {}
START = 0
END = len(numbers)
for i, number in enumerate(numbers):
    if i == START:
        if numbers[i] > numbers[START + 1]:
            _dict[numbers[i]] = numbers[START + 1]
    elif i == END :
       if  numbers[i] > numbers[END - 1]:
        _dict[numbers[i]] = numbers[END - 1]
    else:
        if numbers[i - 1] < numbers[i] < numbers[i + 1]:
            _dict[numbers[i]] = numbers[i]

if __name__ == "__main__":
    print(_dict)
