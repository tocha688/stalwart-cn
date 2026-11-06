/*
 * SPDX-FileCopyrightText: 2020 Stalwart Labs LLC <hello@stalw.art>
 *
 * SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-SEL
 */

include!(concat!(env!("OUT_DIR"), "/locales.rs"));

const TRADITIONAL_CHINESE: [&str; 4] = ["hant", "tw", "hk", "mo"];

/// Locale this build presents.
///
/// The `en-US` copy stays compiled in and `Locale::EnUS` stays the schema
/// default for accounts, but every lookup that would land on `en-US` is served
/// the `zh-CN` copy instead. That is what makes calendar alarms, iTIP
/// invitations and the RSVP page Chinese out of the box, since those all take
/// their language from the account locale. Returning `&EN_US_LOCALES` here
/// restores the original English output.
fn preferred() -> &'static Locale {
    locale("zh-CN").unwrap_or(&EN_US_LOCALES)
}

fn resolve(locale: &'static Locale) -> &'static Locale {
    if locale.name.eq_ignore_ascii_case("en-US") {
        preferred()
    } else {
        locale
    }
}

pub fn locale_or_default(name: &str) -> &'static Locale {
    if let Some(locale) = locale(name) {
        return resolve(locale);
    }

    let mut subtags = name.split(['_', '-']);
    let language = subtags.next().unwrap_or(name);

    if language.eq_ignore_ascii_case("zh")
        && subtags.any(|subtag| {
            TRADITIONAL_CHINESE
                .iter()
                .any(|variant| subtag.eq_ignore_ascii_case(variant))
        })
    {
        return &ZH_TW_LOCALES;
    }

    locale_by_language(language).map_or_else(preferred, resolve)
}

#[cfg(all(test, stalwart_tests))]
#[rustfmt::skip]
#[path = "../../../../stalwart-tests/unit/common/src/i18n/tests.rs"]
mod tests;
