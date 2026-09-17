class CapabilityRegistry:
    """
    Translates abstract capabilities into runtime-specific tool manifests.
    """

    def __init__(self):
        self._mappings: dict[str, dict[str, str]] = {}

    def register_capability(
        self, abstract_capability: str, target_mappings: dict[str, str]
    ) -> None:
        """
        Registers an abstract capability to its runtime-specific equivalents.
        """
        self._mappings[abstract_capability] = target_mappings

    def get_mapping(self, abstract_capability: str) -> dict[str, str]:
        """
        Retrieves the mapping for a specific abstract capability.
        """
        return self._mappings.get(abstract_capability, {})
