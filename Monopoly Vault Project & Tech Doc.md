# Monopoly Vault: Project & Tech Doc

Oct 7, 2026 · @Ivan Santos

## Overview

Monopoly Vault is a mobile-first web app that lets a family pool their McDonald's Monopoly codes in one shared repository and redeem complete sets together, instead of submitting codes one at a time.

- **Problem:** Players suspect they cannot collect every piece in one go, and codes get lost or double-submitted when two people play separately (Ivan in Kentucky, Ebony in Texas).
- **Users:** Family members who each collect codes, link their accounts, and decide who redeems which set.
- **Scope:** One campaign per year. McDonald's runs Monopoly in October only, so each year starts fresh and no multi-year history is tracked.
- **Distribution:** Built to be shared with the open source community.

## Core features

The app stores codes safely until a set is complete, then helps you redeem them without double-submitting.

- **Code entry:** Add a code by photo (OCR) or by typing it.
- **Collection view:** See what you own against the full board, by color set and by individual piece (for example Boardwalk or Park Place), so you know exactly which piece is missing within a set.
- **Linking and pooling:** Accounts join a shared vault so everyone's codes appear in one combined collection.
- **Privacy:** Codes are shared by default and can be switched to private per code.
- **Ready-to-redeem alert:** The app notifies you when a color set is complete.
- **Copy to redeem:** One tap copies a code so it can be pasted into the McDonald's app, and the app tracks whether it was used.
- **Yearly reset:** Each October campaign is its own season; no multi-year tracking.

## In-app help tooltips

Every screen section and feature in the app has an info icon that opens a help modal explaining how it works. Nothing is shown until the user taps the icon.

- **Hidden by default:** The tooltip content is not visible on the page. It appears only after the user taps the info icon.
- **Opens as a modal:** The help appears in a centered modal over the screen, not as an inline hover bubble, so it works on touch devices.
- **Closing:** The modal closes with a close button, a tap outside it, or the back gesture.
- **Accessible and mobile-first:** The icon is a large touch target with a text label for screen readers, and the modal text is short enough to read on a phone without scrolling much.

| Section or feature | What its help modal explains |
| --- | --- |
| Code entry | How to add a code by photo or by typing, and how to correct a misread |
| Collection view | How pieces and color sets are checked off, and what "missing" means |
| Linking and pooling | How to join a vault and how combined progress is calculated |
| Privacy toggle | That codes are shared by default, how to mark one private, and what private means |
| Ready-to-redeem alert | When a set counts as complete and what the alert does |
| Copy to redeem | What happens when a code is copied and why it becomes Pending |
| Redemption status | The difference between Available, Pending, and Used, and the next-session question |
| OCR photo capture | How to take a clear photo, the confirm step, and where the original photo is kept |
| Yearly reset | That each October campaign starts fresh |

## Redemption tracking

Copying a code moves it to Pending, and the next visit asks whether it was actually used, so nothing is double-submitted and nothing is lost.

1. A complete set is ready, and users decide who redeems what (for example Ebony redeems yellow, Ivan redeems red).
2. The user taps copy on a code and pastes it into the McDonald's app.
3. The code immediately becomes **Pending**. It stays usable but is flagged as possibly used.
4. On the next session, the app asks: "In your last session you copied this code. Did you submit it?"
5. If **yes**, the code is marked **Used** with a date and timestamp and who applied it.
6. If **no**, the code returns to **Available** in the repository.
7. Until the question is answered, the code stays Pending.

| Status | Meaning | Changes when |
| --- | --- | --- |
| Available | Collected, not yet copied | User copies it |
| Pending | Copied, outcome unconfirmed | User answers the next-session prompt |
| Used | Confirmed submitted, timestamped | Final state |

## OCR photo capture

Users photograph a sticker or coupon code and the app extracts the code text, so nobody has to type long codes by hand.

1. Open the camera from the app and photograph the sticker.
2. The image is uploaded and the OCR engine reads the code.
3. The extracted code is shown back for a quick confirmation before saving, in case of misreads.
4. The code is written to the database as an Available code.
5. The original photo stays saved in the repository, linked to that code, as a backup record for future confirmation or disputes.

The camera button should be front and center on the phone layout, since this is the main way codes get in.

## Accounts, vaults, and privacy

Every code is shared with the vault by default, and a user can mark any individual code private.

- Each person has their own account.
- A **vault** is the shared household space. Linking with another person means both accounts are members of the same vault.
- The vault's pooled view shows every shared code from every member, so set completion is calculated across the whole household.
- Each code carries a visibility flag: **Shared** (default) or **Private**. Private codes are visible only to their owner and do not count toward the pooled view.
- Switching a code to Private is always a deliberate user action, never automatic.
- Login is a simple token-based sign-in, since the user base is a small family.

## Tech stack

A mobile-first Progressive Web App on a Python backend, built entirely from free, open-source parts so it is easy to share publicly.

| Layer | Proposed choice | Why |
| --- | --- | --- |
| Frontend | PWA built with React or Vue | Add to home screen, app-like feel, no app store |
| Backend API | Python with FastAPI | Lightweight, free, same language as the OCR library |
| Database | PostgreSQL | Structured data, runs in its own container |
| OCR | Tesseract | Free and open source, Python-friendly |
| Image storage | Mounted volume on the NAS | Photos on disk, file path stored in Postgres |
| Auth | Lightweight JWT login | Simple enough for a small family |

**Design priority:** mobile first. The PWA is built and tested on phone screens before desktop, with camera access for OCR and large touch targets for the copy-to-redeem flow.

## Data model

Four core tables cover everything: users, vaults, the membership link between them, and the codes themselves.

| Table | Key fields | Purpose |
| --- | --- | --- |
| users | id, name, login credentials | One row per person |
| vaults | id, name, campaign year | The shared household space |
| vault\_members | user id, vault id | Links users to vaults |
| codes | code text, piece, color set, owner, vault, visibility, status, photo path, collected at, copied at, confirmed at | One row per sticker code |

- **Visibility** defaults to Shared and changes to Private only when the user chooses.
- **Status** is Available, Pending, or Used, with a timestamp for when it was copied and when it was confirmed.
- **Photo path** points to the saved original image on the NAS.

## Hosting and deployment

The app runs as new containers in the existing Docker Compose stack on the homelab, served from its own subdomain on nexmolab.us.

- **Subdomain:** a new one on nexmolab.us (for example monopoly.nexmolab.us), reachable from both phones.
- **Containers:** one for the FastAPI backend, one for PostgreSQL, and one for the frontend, added to the current Compose setup.
- **Photo storage:** a volume mounted from the NAS, with only file paths kept in the database.
- **Backups:** include the Postgres data and photo folder in the existing backup script.

## Open questions and build order

The suggested order builds the core vault first and adds OCR and linking once the basics work.

1. Backend and database: users, codes, and the Available, Pending, Used statuses.
2. Mobile-first PWA shell with manual code entry and the collection view by set and piece.
3. Copy-to-redeem flow with the next-session confirmation prompt.
4. Vaults, linking, and the shared/private toggle.
5. OCR photo capture with confirm step and saved original photo.
6. Ready-to-redeem alerts, then deploy on the homelab and test on both phones.

**Open questions**

- [x] **Do private codes count toward set completion?** Yes, for the owner only. A private code counts toward its owner's own sets and never appears in the pooled view.
- [x] **Where does the official list of pieces and color sets come from each year?** The pieces come from the items purchased at McDonald's. The 2026 Official Rules also list all 28 properties (#901 to #928) and the 10 winning combinations, so each year's set list can be seeded from the published rules.
- [ ] **How well does OCR read real stickers?** Post-development test: try a few actual codes once the capture flow is built.
- [ ] **Do the promotion's rules allow sharing codes between family members?** Not confirmed. Working assumption: internal household use only. The 2026 Official Rules, however, require one McDonald's account per person, say a winning combination must be collected in a single person's game account, and prohibit consolidating pieces from multiple participants into one account (Rule 13.A) and transferring pieces without written approval (Rule 4.F). Check before building any flow that moves codes between people's accounts.
