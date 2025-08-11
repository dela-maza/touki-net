from enum import  Enum
class ClientType(Enum):
    RIGHT_HOLDER = "RIGHT_HOLDER"       # 権利者
    OBLIGATION_HOLDER = "OBLIGATION_HOLDER"  # 義務者
    APPLICANT = "APPLICANT"             # 申請人

    @property
    def default_entries_section(self) -> str:
        # config.ini のセクション名を一元管理
        return {
            ClientType.RIGHT_HOLDER:      "DEFAULT_ENTRIES_RIGHT_HOLDER",
            ClientType.OBLIGATION_HOLDER: "DEFAULT_ENTRIES_OBLIGATION_HOLDER",
            ClientType.APPLICANT:         "DEFAULT_ENTRIES_APPLICANT",
        }[self]
