-- À exécuter dans l'éditeur SQL de Supabase (SQL Editor > New Query)

create table evenements_personnalises (
    id uuid primary key default gen_random_uuid(),
    nom text not null,
    date_evenement date not null,
    message_suggere text,
    ajoute_par text,
    created_at timestamp with time zone default now()
);

-- Autorise la lecture/écriture publique (adapté à un prototype interne,
-- à restreindre avec une vraie authentification si le projet passe en production)
alter table evenements_personnalises enable row level security;

create policy "Lecture publique" on evenements_personnalises
    for select using (true);

create policy "Écriture publique" on evenements_personnalises
    for insert with check (true);

create policy "Suppression publique" on evenements_personnalises
    for delete using (true);
