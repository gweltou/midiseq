from midiseq.ports import InputPort, OutputPort


def test_input_port():
    print("Test Input port")
    input_port = InputPort(0)
    print(input_port.name)

    is_open = input_port.isOpen()
    assert is_open

    input_port.close()
    is_open = input_port.isOpen()
    assert not is_open


def test_output_port():
    print("Test Output port")
    output_port = OutputPort(0)
    print(output_port.name)

    is_open = output_port.isOpen()
    assert is_open

    # Push a few mockup midi messages
    output_port.push(0.0, [144, 48, 127])
    output_port.push(0.1, [144, 50, 127])
    output_port.push(0.5, [128, 48, 0])
    output_port.push(1.0, [144, 50, 0]) # This should be treated as a note off as well

    assert len(output_port._events) == 4

    output_port.process(0.0)
    assert len(output_port._events) == 3

    for i in range(5):
        output_port.process(0.25)
    
    assert len(output_port._events) == 0

    output_port.close()
    is_open = output_port.isOpen()
    assert not is_open
