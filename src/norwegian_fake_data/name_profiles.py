"""International distributions and explicit approximations; no network access."""

import gzip
import json
from collections import Counter
from functools import cache, lru_cache
from importlib.resources import files
from itertools import accumulate


@cache
def snapshot(locale: str) -> dict:
    resource = files("norwegian_fake_data").joinpath(f"data/names-{locale}.json.gz")
    return json.loads(gzip.decompress(resource.read_bytes()))


def nearest(year: int, years: tuple[int, ...]) -> int:
    return min(years, key=lambda candidate: (abs(candidate - year), candidate))


@cache
def years(locale: str, section: str) -> tuple[int, ...]:
    return tuple(sorted({int(key.split(":")[0]) for key in snapshot(locale)[section]}))


def score_groups(rows, scores):
    """SSA-weighted SNI tertiles; ties share a group, never infer income probabilities."""
    matched = [
        (name, weight, scores[name.casefold()])
        for name, weight in rows
        if name.casefold() in scores
    ]
    matched.sort(key=lambda row: (row[2], row[0]))
    total = sum(weight for _, weight, _ in matched)
    mass = total / sum(weight for _, weight in rows)
    if not total or mass < 0.75:
        raise ValueError(f"US SES matched coverage {mass:.1%} is below the required 75%.")
    cumulative, cutoffs = 0, []
    for _, weight, score in matched:
        cumulative += weight
        while len(cutoffs) < 2 and cumulative * 3 >= total * (len(cutoffs) + 1):
            cutoffs.append(score)
    groups = {key: [] for key in ("lower", "middle", "higher")}
    for name, weight, score in matched:
        group = "lower" if score <= cutoffs[0] else "middle" if score <= cutoffs[1] else "higher"
        groups[group].append([name, weight])
    if any(not rows for rows in groups.values()):
        raise ValueError("US SES scores do not support three nonempty background groups.")
    return groups, mass, tuple(cutoffs)


@lru_cache(maxsize=512)
def distribution(
    locale: str,
    year: int,
    category: str,
    fallback: str,
    background: str,
    nssec: int | None,
    background_fallback: str,
) -> tuple[tuple[tuple[str, int], ...], dict]:
    data = snapshot(locale)
    annual = years(locale, "first_names")
    source_year = year
    section = "first_names"
    reasons = []
    if year not in annual:
        if fallback == "historical" and locale == "england" and year < annual[0]:
            section = "historical"
            source_year = nearest(year, years(locale, section))
        elif fallback == "nearest":
            source_year = nearest(year, annual)
        else:
            raise ValueError(
                f"{locale} annual first-name data covers {annual[0]}–{annual[-1]}; "
                f"birth year {year} is outside this range. Use --name-fallback nearest"
                + (" or historical for older England names." if locale == "england" else ".")
            )
    rows = data[section][f"{source_year}:{category}"]
    method = "historical_rank" if section == "historical" else "published_counts"
    if section == "historical":
        reasons.append("historical top-100 list with heuristic 1/rank weights")
    if source_year != year:
        reasons.append("first-name source year differs from birth year")
    meta = {
        "first_name_year": source_year,
        "sampling_method": method,
        "first_name_approximate": section == "historical" or source_year != year,
        "source_geography": data["geography"],
        "dataset_version": data["dataset_version"],
        "background_applied": "any",
        "background_method": "none",
        "background_period": None,
        "background_geography": None,
        "background_matched_mass": None,
        "background_cutoffs": None,
    }
    if background != "any" or nssec is not None:
        try:
            if locale == "england":
                if not 2001 <= year <= 2024:
                    raise ValueError("England occupational background data covers 2001–2024.")
                classes = (
                    (nssec,)
                    if nssec is not None
                    else {
                        "lower": (5, 6, 7),
                        "middle": (3, 4),
                        "higher": (1, 2),
                    }[background]
                )
                counts = Counter()
                for cls in classes:
                    counts.update(dict(data["occupational"][f"{year}:{category}:{cls}"]))
                rows = sorted(counts.items())
                meta.update(
                    background_method="parental_occupation_counts",
                    background_period=str(year),
                    background_geography="England and Wales",
                    background_applied=f"nssec-{nssec}" if nssec else background,
                    sampling_method="published_counts",
                    first_name_year=year,
                    first_name_approximate=False,
                )
            else:
                if not 1982 <= year <= 2017:
                    raise ValueError("Experimental US SES background data covers 1982–2017.")
                groups, mass, cutoffs = score_groups(rows, data["ses_scores"])
                rows = groups[background]
                meta.update(
                    background_method="experimental_sni_tertiles",
                    background_period=data["ses_period"],
                    background_geography="California",
                    background_applied=background,
                    background_matched_mass=mass,
                    background_cutoffs=",".join(str(value) for value in cutoffs),
                    first_name_approximate=True,
                )
                reasons.append("experimental California neighbourhood-income score overlay")
        except ValueError as exc:
            if background_fallback != "unconditioned":
                raise ValueError(
                    f"{exc} Use --background-fallback unconditioned to omit the background filter."
                ) from None
            reasons.append(f"requested background not applied: {exc}")
    meta["approximation_reasons"] = "; ".join(reasons)
    return tuple((name, weight) for name, weight in rows), meta


@lru_cache(maxsize=16)
def surname_distribution(locale: str, story_year: int):
    data = snapshot(locale)
    if locale == "england":
        return data["surnames"]["curated"], None
    source_year = nearest(story_year, years(locale, "surnames"))
    return data["surnames"][str(source_year)], source_year


@lru_cache(maxsize=512)
def prepared_distribution(*args):
    rows, metadata = distribution(*args)
    names, weights = zip(*rows, strict=True)
    return names, tuple(accumulate(weights)), metadata


@lru_cache(maxsize=16)
def prepared_surnames(locale: str, story_year: int):
    rows, year = surname_distribution(locale, story_year)
    names, weights = zip(*rows, strict=True)
    return names, tuple(accumulate(weights)), year
