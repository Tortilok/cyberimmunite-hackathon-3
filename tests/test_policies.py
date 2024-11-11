import os
import sys
import unittest


__location__: str = os.path.dirname(os.path.abspath(__file__))
monitor_path: str = os.path.join(__location__,
                                 os.pardir,
                                 'management-system', 'modules', 'monitor', 'module')

if not os.path.exists:
    print('failed to find policies in', monitor_path)
    exit(1)
else:
    sys.path.insert(1, monitor_path)
    from policies import policies, check_operation


length: int = len(policies)
event_id: int = 0


def next_event(self) -> int:
    global event_id

    event_id += 1
    return event_id


class TestOperation(unittest.TestCase):
    event = next_event

    def test_true(self):
        result = check_operation(self.event(), {
            'source': policies[1]['src'],
            'deliver_to': policies[1]['dst']
        })

        self.assertEqual(result, True)

    def test_false(self):
        result = check_operation(self.event(), {
            'source': 'foo',
            'deliver_to': 'bar'
        })

        self.assertEqual(result, False)

    def test_true2(self):
        result = check_operation(self.event(), {
            'source': policies[2]['src'],
            'deliver_to': policies[2]['dst']
        })

        self.assertEqual(result, True)

    def test_blank(self):
        result = check_operation(self.event(), {
            'source': '',
            'deliver_to': ''
        })

        self.assertEqual(result, False)

    def test_com_mobile(self):
        ops = (
            ('com-mobile', 'profile-client', True),
            ('profile-client', 'com-mobile', True),
            ('com-mobile', 'sender-car', False)
        )

        for op in ops:
            result = check_operation(self.event(), {
                'source': op[0],
                'deliver_to': op[1]
            })

            self.assertEqual(result, op[2])

    def test_profile_client(self):
        ops = (
            ('profile-client', 'com-mobile', True),
            ('profile-client', 'manage-drive', True),
            ('profile-client', 'bank-pay', True),
            ('manage-drive', 'profile-client', True),
            ('bank-pay', 'profile-client', True),
            ('com-mobile', 'profile-client', True),
            ('com-mobile', 'control-drive', False),
            ('com-mobile', 'sender-car', False),
            ('com-mobile', 'verify', False)
        )

        for op in ops:
            result = check_operation(self.event(), {
                'source': op[0],
                'deliver_to': op[1]
            })

            self.assertEqual(result, op[2])

    def test_manage_drive(self):
        ops = (
            ('profile-client', 'manage-drive', True),
            ('manage-drive', 'profile-client', True),
            ('manage-drive', 'verify', True),
            ('control-drive', 'manage-drive', True),
            ('manage-drive', 'auth', False),
            ('manage-drive', 'sender-car', False),
            ('receiver-car', 'manage-drive', False)
        )

        for op in ops:
            result = check_operation(self.event(), {
                'source': op[0],
                'deliver_to': op[1]
            })

            self.assertEqual(result, op[2])

    def test_bank_pay(self):
        ops = (
            ('bank-pay', 'profile-client', True),
            ('profile-client', 'bank-pay', True),
            ('manage-drive', 'bank-pay', False)
        )

        for op in ops:
            result = check_operation(self.event(), {
                'source': op[0],
                'deliver_to': op[1]
            })

            self.assertEqual(result, op[2])

    def test_verify(self):
        ops = (
            ('verify', 'auth', True),
            ('manage-drive', 'verify', True),
            ('verify', 'sender-car', False)
        )

        for op in ops:
            result = check_operation(self.event(), {
                'source': op[0],
                'deliver_to': op[1]
            })

            self.assertEqual(result, op[2])

    def test_auth(self):
        ops = (
            ('verify', 'auth', True),
            ('auth', 'sender-car', True),
            ('manage-drive', 'auth', False)
        )

        for op in ops:
            result = check_operation(self.event(), {
                'source': op[0],
                'deliver_to': op[1]
            })

            self.assertEqual(result, op[2])

    def test_receiver_car(self):
        ops = (
            ('receiver-car', 'control-drive', True),
            ('receiver-car', 'manage-drive', False)
        )

        for op in ops:
            result = check_operation(self.event(), {
                'source': op[0],
                'deliver_to': op[1]
            })

            self.assertEqual(result, op[2])

    def test_sender_car(self):
        ops = (
            ('auth', 'sender-car', True),
            ('control-drive', 'sender-car', True),
            ('manage-drive', 'sender-car', False)
        )

        for op in ops:
            result = check_operation(self.event(), {
                'source': op[0],
                'deliver_to': op[1]
            })

            self.assertEqual(result, op[2])

    def test_control_drive(self):
        ops = (
            ('control-drive', 'manage-drive', True),
            ('control-drive', 'sender-car', True),
            ('receiver-car', 'control-drive', True),
            ('manage-drive', 'control-drive', False),
            ('profile-client', 'control-drive', False),
            ('control-drive', 'bank-pay', False)
        )

        for op in ops:
            result = check_operation(self.event(), {
                'source': op[0],
                'deliver_to': op[1]
            })

            self.assertEqual(result, op[2])


if __name__ == '__main__':
    unittest.main(verbosity=2)
