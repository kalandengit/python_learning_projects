import { Column, Entity, OneToMany, PrimaryColumn } from 'typeorm';
import { Ayah } from './ayah.entity';

export enum RevelationPlace {
  Meccan = 'meccan',
  Medinan = 'medinan',
}

@Entity({ name: 'surahs' })
export class Surah {
  /** Canonical surah number, 1–114. */
  @PrimaryColumn({ type: 'int' })
  id!: number;

  @Column({ type: 'varchar' })
  nameArabic!: string;

  @Column({ type: 'varchar' })
  nameTransliteration!: string;

  @Column({ type: 'varchar' })
  nameTranslation!: string;

  @Column({ type: 'varchar', default: RevelationPlace.Meccan })
  revelationPlace!: RevelationPlace;

  @Column({ type: 'int' })
  ayahCount!: number;

  @OneToMany(() => Ayah, (ayah) => ayah.surah)
  ayahs!: Ayah[];
}
