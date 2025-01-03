from io import StringIO
import pytest
from unittest.mock import patch, call

from alarmd import debug
from alarmd.rest import app
from alarmd.dsl import read_config
from alarmd.state import event_processor

from test_state import SETUP, SENSOR_SETUP

@pytest.fixture
def client():
    """Fixture for creating a test client."""
    with app.test_client() as client:
        yield client

def test_status_route(client):
    mock_file = StringIO(SETUP + """
*:
    CmdSecond > second
    ;

initial:
    CmdOther > second
    ;

second:
    > DONE
    ;
    """)
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        initial_name = read_config(mock_file)

        response = client.get("/cmd/Second")
        assert response.status_code == 200
        assert response.json == {"CmdSecond": "OK"}

        event_processor(initial_name)

        response = client.get("/state")
        assert response.status_code == 200
        assert response.json == {"state": "DONE"}


def test_command_route(client):
    mock_file = StringIO(SETUP + """
*:
    CmdSecond > second
    CmdOther > other
    ;

initial:
    | set_bit('Siren5', 1)
    quit > DONE
    ;

second:
    | set_bit('Siren6', 0)
    quit > DONE
    ;

other:
    | set_bit('Siren6', 1)
    > DONE
    ;
    """)
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        initial_name = read_config(mock_file)

        response = client.get("/cmd/NonExistent")
        assert response.status_code == 404

        response = client.get("/cmd/Second")
        assert response.status_code == 200
        assert response.json == {"CmdSecond": "OK"}

        response = client.get("/cmd/Other")
        assert response.status_code == 200
        assert response.json == {"CmdOther": "OK"}

        event_processor(initial_name)
        assert mock_output.call_count == 3
        mock_output.assert_has_calls([call(5, 1), call(6, 0), call(6, 1)])


def test_404_route(client):
    """Test accessing an undefined route."""
    response = client.get("/undefined")
    assert response.status_code == 404


def test_sensor_route(client):
    mock_file = StringIO(SETUP + SENSOR_SETUP)
    with patch('RPi.GPIO.input') as mock_input, \
            patch('RPi.GPIO.add_event_detect') as mock_add_event_detect, \
            patch('RPi.GPIO.setup') as mock_setup:
        mock_input.return_value = 12
        initial_name = read_config(mock_file)

        response = client.get("/sensor/Bedroom")
        assert response.status_code == 200
        assert response.json == {"value": 12}

        response = client.get("/sensor/NonExistent")
        assert response.status_code == 404

        response = client.get("/sensor/Siren5")
        assert response.status_code == 404
