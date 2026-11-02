import unittest

from fabrica.domain import Expedient
from fabrica.notifications import NotificationService


class FakeMessenger:
    def __init__(self):
        self.messages = []

    def send(self, recipient, message):
        self.messages.append((recipient, message))
        return "notification-1"


class NotificationServiceTests(unittest.TestCase):
    def test_notifies_through_the_expedients_origin_channel(self):
        messenger = FakeMessenger()
        service = NotificationService()
        service.register("telegram", messenger)
        expedient = Expedient.start(
            "prepare-report", "1.0", "empresa-demo", "telegram", "user-42", {}
        )
        expedient.move_to("completed")

        notification_id = service.notify(expedient, "El informe está listo")

        self.assertEqual(notification_id, "notification-1")
        self.assertEqual(messenger.messages, [("user-42", "El informe está listo")])
        self.assertEqual(expedient.timeline[-1]["type"], "notification_sent")

    def test_fails_when_the_channel_has_no_adapter(self):
        service = NotificationService()
        expedient = Expedient.start(
            "prepare-report", "1.0", "empresa-demo", "email", "user@example.com", {}
        )

        with self.assertRaises(KeyError):
            service.notify(expedient, "El informe está listo")


if __name__ == "__main__":
    unittest.main()
