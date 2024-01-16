import os
from typing import Dict, Optional

from discord import Locale
from discord import app_commands
from fluent.runtime import FluentLocalization, FluentResourceLoader

from helpers import constants

class CommandTranslator(app_commands.Translator):
    """Translates command names and descriptions."""
    def __init__(self) -> None:
        self.loader: FluentResourceLoader = None
        self.l10n: Dict[Locale, FluentLocalization] = {}

    async def load(self) -> None:
        package_dir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(package_dir, "l10n", "{locale}")
        self.loader = FluentResourceLoader(path)
        for locale in constants.SUPPORTED_LOCALES:
            self.l10n[locale] = FluentLocalization(
                [str(locale), str(constants.DEFAULT_LOCALE)], ["commands.ftl"], self.loader)

    async def translate(
        self,
        string: app_commands.locale_str,
        locale: Locale,
        context: app_commands.TranslationContext
    ) -> Optional[str]:
        localization = self.l10n.get(locale)
        if localization is None:
            localization = self.l10n.get(constants.DEFAULT_LOCALE)
            if localization is None:
                return None

        message = str(string)

        if context.location is app_commands.TranslationContextLocation.command_name:
            message = "cmd-" + message
        elif context.location is app_commands.TranslationContextLocation.command_description:
            message = "desc-" + message
        elif context.location is app_commands.TranslationContextLocation.parameter_name:
            message = "arg-" + message
        elif context.location is app_commands.TranslationContextLocation.parameter_description:
            message = "arg-desc-" + message

        translation = localization.format_value(message, string.extras)
        if message == translation:
            return None

        return translation
