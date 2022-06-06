from solo.exec_python import ExecPython

"""
     A test with calculations of a 3D assimilation window
"""

types = {
    'current_cycle': 'solo.date.JediDate',
    'window_offset': 'solo.date.DateIncrement',
    'window_length': 'solo.date.DateIncrement',
    'bg_step': 'solo.date.DateIncrement',
}

config = {
    'current_cycle': '2021-07-01T00:00:00',
    'window_length': 'PT6H',
    'window_offset': 'PT3H',
    'bg_step': 'PT6H',
    'window': {
        'analysis_time': 'current_cycle',
        'window_begin': 'current_cycle - window_offset - window_length',
        'window_end': 'current_cycle + window_offset',
        'background_time': 'current_cycle - bg_step',
        'background_steps': '[$(bg_step)]',
        'py_types': types
    }
}

def test_exec():
    result = {'bg_step': 'PT6H',
                 'current_cycle': '2021-07-01T00:00:00',
                 'window': {'analysis_time': '2021-07-01T00:00:00Z',
                            'background_steps': '[$(bg_step)]',
                            'background_time': '2021-06-30T18:00:00Z',
                            'py_types': {'bg_step': 'solo.date.DateIncrement',
                                         'current_cycle': 'solo.date.JediDate',
                                         'window_length': 'solo.date.DateIncrement',
                                         'window_offset': 'solo.date.DateIncrement'},
                            'window_begin': '2021-06-30T15:00:00Z',
                            'window_end': '2021-07-01T03:00:00Z'},
                 'window_length': 'PT6H',
                 'window_offset': 'PT3H'}
    ExecPython(config, ['window'], 'py_types')
    assert config == result
