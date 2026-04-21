import multiprocessing as mp
from TikTokLive import TikTokLiveClient
from TikTokLive.events import LikeEvent, CommentEvent, GiftEvent, JoinEvent

def tiktok_worker(username, queue):

    def on_like(event: LikeEvent):
        queue.put(("like", getattr(event.user, "unique_id", "?"), getattr(event, "total_likes", "?")))

    def on_comment(event: CommentEvent):
        queue.put(("chat", getattr(event.user, "unique_id", "?"), getattr(event, "comment", "?")))

    def on_gift(event: GiftEvent):
        gift_name = getattr(getattr(event, "gift", None), "name", "?")
        from_user = getattr(event.user, "unique_id", "?")
        # Si to_user n'est pas renseigné, on considère que c'est l'hôte (username)
        to_user = getattr(getattr(event, "to_user", None), "unique_id", None)
        if not to_user or to_user == "?":
            to_user = username
        queue.put(("cadeau", f"{from_user} → {to_user}", gift_name))

    def on_join(event: JoinEvent):
        # Envoie JoinEvent comme un message de chat (comportement initial)
        queue.put(("chat", getattr(event.user, "unique_id", "?"), "a rejoint le live"))

    client = TikTokLiveClient(unique_id=username)
    client.on(LikeEvent)(on_like)
    client.on(CommentEvent)(on_comment)
    client.on(GiftEvent)(on_gift)
    client.on(JoinEvent)(on_join)
    try:
        client.run()
    except Exception as e:
        queue.put(("error", str(e), ""))

def start_tiktok_process(username):
    queue = mp.Queue()
    proc = mp.Process(target=tiktok_worker, args=(username, queue), daemon=True)
    proc.start()
    return proc, queue
