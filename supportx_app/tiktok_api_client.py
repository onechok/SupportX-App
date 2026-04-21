from TikTokLive import TikTokLiveClient
from TikTokLive.events import *
from threading import Thread

class TikTokAPIClient:
    def __init__(self, username, on_event_callback):
        self.username = username
        self.on_event_callback = on_event_callback
        self.client = TikTokLiveClient(unique_id=username)
        self._thread = None
        self._setup_events()

    def _setup_events(self):
        @self.client.on(LikeEvent)
        def on_like(event: LikeEvent):
            # LikeEvent: event.user (ExtendedUser), total_likes
            self.on_event_callback("like", getattr(event.user, "unique_id", "?"), getattr(event, "total_likes", "?"))

        @self.client.on(CommentEvent)
        def on_comment(event: CommentEvent):
            # CommentEvent: event.user (ExtendedUser), event.comment (str)
            self.on_event_callback("chat", getattr(event.user, "unique_id", "?"), getattr(event, "comment", "?"))

        @self.client.on(GiftEvent)
        def on_gift(event: GiftEvent):
            # GiftEvent: event.user (ExtendedUser), event.gift (Gift)
            gift_name = getattr(getattr(event, "gift", None), "name", "?")
            self.on_event_callback("cadeau", getattr(event.user, "unique_id", "?"), gift_name)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = Thread(target=self.client.run, daemon=True)
        self._thread.start()

    def stop(self):
        self.client.stop()
