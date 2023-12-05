# from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey, func
# from sqlalchemy.orm import relationship
# from datetime import datetime


# class UserDB(Base):
#     __tablename__ = 'user'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column('id', Integer, primary_key=True)
#     username = Column('username', String)
#     email = Column('email', String)
#     registered_at = Column('registered_at', TIMESTAMP, default=func.utcnow())
#
#     def __init__(self, username, email, registered_at=datetime.utcnow()):
#         super().__init__()
#         self.username = username
#         self.email = email
#         self.registered_at = registered_at
#
#     def __repr__(self):
#         return f'({self.id}) {self.username} {self.email} ' \
#                f'registered at {self.registered_at}'


# class TournamentDB(Base):
#     __tablename__ = 'tournament'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column('id', Integer, primary_key=True)
#     tournament_eesl_id = Column('tournament_eesl_id', Integer,
#                                 nullable=True, unique=True)
#     title = Column('title', String(255),
#                    nullable=False)
#     description = Column('description',
#                          Text, default='')
#     tournament_logo_url = Column('tournament_logo_url',
#                                  String(255), nullable=True)
#     fk_season = Column(Integer, ForeignKey('season.year', ondelete="CASCADE"),
#                        nullable=False)
#
#     # seasons = relationship('SeasonDB',
#     #                        back_populates='tournaments')
#     matches = relationship('MatchDB', cascade="all, delete-orphan",
#                            back_populates="tournaments", passive_deletes=True)
#     fk_teams_id = relationship('TeamDB',
#                                secondary='team_tournament',
#                                back_populates='fk_tournaments_id')
#     # lazy='subquery')

#
# class TeamDB(Base):
#     __tablename__ = 'team'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column('id', Integer, primary_key=True)
#     team_eesl_id = Column('team_eesl_id', Integer,
#                           nullable=True, unique=True)
#     title = Column('title', String(30),
#                    nullable=False)
#     description = Column('description', Text,
#                          default='')
#     team_logo_url = Column('team_logo_url', String(255),
#                            nullable=True)
#
#     fk_tournaments_id = relationship('TournamentDB',
#                                      secondary='team_tournament',
#                                      back_populates='fk_teams_id',
#                                      cascade="save-update, merge",
#                                      )
#
#     matches = relationship(
#         'MatchDB',
#         primaryjoin="or_(TeamDB.id==MatchDB.fk_team_a, TeamDB.id==MatchDB.fk_team_b)",
#         back_populates='teams', overlaps="team_a_matches, team_b_matches")
#
#
# class TeamTournamentDB(Base):
#     __tablename__ = 'team_tournament'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column('id', Integer, primary_key=True)
#     fk_tournament = Column(Integer, ForeignKey('tournament.id', ondelete='CASCADE'),
#                            nullable=False)
#     fk_team = Column(Integer, ForeignKey('team.id', ondelete='CASCADE'),
#                      nullable=False)
#
#     fk_players_id = relationship('PlayerDB',
#                                  secondary='player_team_tournament',
#                                  back_populates='fk_team_tournaments_id',
#                                  cascade="save-update, merge",
#                                  )
#
#
# class MatchDB(Base):
#     __tablename__ = 'match'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column('id', Integer, primary_key=True)
#     match_eesl_id = Column('match_eesl_id', Integer,
#                            nullable=True, unique=True)
#     field_length = Column('field_length', Integer,
#                           nullable=True, default=92)
#     match_date = Column('match_date', TIMESTAMP,
#                         nullable=True)
#     eesl_id_team_a = Column('eesl_id_team_a', Integer,
#                             nullable=True)
#     eesl_id_team_b = Column('eesl_id_team_b', Integer,
#                             nullable=True)
#
#     fk_team_a = Column(Integer, ForeignKey(
#         'team.id', ondelete="CASCADE"), nullable=False)
#     fk_team_b = Column(Integer, ForeignKey(
#         'team.id', ondelete="CASCADE"), nullable=False)
#     fk_tournament = Column(Integer, ForeignKey(
#         'tournament.id', ondelete="CASCADE"), nullable=True)
#     # team_a = relationship('TeamDB', foreign_keys=[fk_team_a],
#     #                       backref='team_a_matches')
#     # team_b = relationship('TeamDB', foreign_keys=[fk_team_b],
#     #                       backref='team_b_matches')
#     tournaments = relationship('TournamentDB',
#                                back_populates='matches')
#     results = relationship('MatchResultDB', cascade="all, delete-orphan",
#                            back_populates="matches", passive_deletes=True)
#
#     fk_match_players_id = relationship('PlayerTeamTournamentDB',
#                                        secondary='player_match',
#                                        back_populates='fk_matches_id',
#                                        cascade="save-update, merge",
#                                        )
#     teams = relationship(
#         'TeamDB',
#         primaryjoin="or_(TeamDB.id==MatchDB.fk_team_a, TeamDB.id==MatchDB.fk_team_b)",
#         back_populates='matches', overlaps="team_a_matches, team_b_matches")
#
#
# class MatchResultDB(Base):
#     __tablename__ = 'match_result'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column('id', Integer, primary_key=True)
#     score_team_a = Column('score_team_a', Integer,
#                           nullable=True)
#     score_team_b = Column('score_team_b', Integer,
#                           nullable=True)
#     fk_match = Column(Integer, ForeignKey(
#         'match.id', ondelete="CASCADE"), nullable=False, unique=True)
#
#     matches = relationship('MatchDB',
#                            back_populates='results')
#
#
# class PlayerDB(Base):
#     __tablename__ = 'player'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column('id', Integer, primary_key=True)
#     player_eesl_id = Column('player_eesl_id', Integer,
#                             nullable=True, unique=True)
#     player_full_name = Column('player_full_name', String(60),
#                               nullable=False)
#     player_first_name = Column('player_first_name', String(30),
#                                nullable=False)
#     player_second_name = Column('player_second_name', String(30),
#                                 nullable=False)
#     player_img_url = Column('player_img_url', String(255),
#                             nullable=True)
#     player_dob = Column('player_dob', TIMESTAMP,
#                         nullable=True)
#
#     fk_team_tournaments_id = relationship('TeamTournamentDB',
#                                           secondary='player_team_tournament',
#                                           back_populates='fk_players_id',
#                                           cascade="save-update, merge",
#                                           )
#
#
# class PlayerTeamTournamentDB(Base):
#     __tablename__ = 'player_team_tournament'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column('id', Integer, primary_key=True)
#     fk_player = Column(Integer, ForeignKey('player.id', ondelete='CASCADE'),
#                        nullable=False)
#     fk_team_tournament = Column(Integer, ForeignKey('team_tournament.id', ondelete='CASCADE'),
#                                 nullable=False)
#     player_number = Column('player_number', Integer,
#                            nullable=True, default=0)
#     player_position = Column('player_position', String(5),
#                              nullable=True)
#
#     fk_matches_id = relationship('MatchDB',
#                                  secondary='player_match',
#                                  back_populates='fk_match_players_id',
#                                  cascade="save-update, merge",
#                                  )
#
#
# class PlayerMatchDB(Base):
#     __tablename__ = 'player_match'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column('id', Integer, primary_key=True)
#     fk_player_team_tournament = Column(Integer, ForeignKey(
#         'player_team_tournament.id',
#         ondelete='CASCADE'), nullable=False)
#     fk_match = Column('fk_match', ForeignKey(
#         'match.id', ondelete="CASCADE"), nullable=False)
#     player_number = Column('player_number', Integer,
#                            nullable=True, default=0)
#     player_position = Column('player_position', String(5),
#                              nullable=True)
