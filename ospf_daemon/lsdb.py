import time

MAX_AGE = 3600

class LSDB:
    def __init__(self):
        self.db = {}

    def add_lsa(self, lsa_dict):
        adv = lsa_dict['adv_router']
        seq = lsa_dict['seq']
        now = time.time()
        if adv not in self.db or seq > self.db[adv]['seq']:
            self.db[adv] = {
                'seq': seq,
                'timestamp': now,
                'links': lsa_dict['links']
            }

    def purge_expired(self):
        now = time.time()
        expired = [r for r, data in self.db.items() if now - data['timestamp'] > MAX_AGE]
        for r in expired:
            del self.db[r]

    def get_links(self):
        result = {}
        for r, data in self.db.items():
            result[r] = []
            for link_id, _, _, metric in data['links']:
                result[r].append((link_id, metric))
        return result

lsdb = LSDB()